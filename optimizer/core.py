"""Pure decisions. No I/O, model calls, inferred grants or credential access."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
import hashlib
import math


def timestamp(value):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a timestamp")
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("Timestamp requires a timezone")
        result = dt.timestamp()
    else:
        raise ValueError("Missing timestamp")
    if not 0 < result < 32503680000:
        raise ValueError("Timestamp out of range")
    return result


def iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Window:
    key: str
    used_percent: float
    resets_at: float
    duration_minutes: int


@dataclass(frozen=True)
class Status:
    account_id: str
    observed_at: float
    windows: tuple[Window, ...]
    model_ids: tuple[str, ...] = ()
    verified: bool = False
    ordinary_usage_allowed: bool | None = None
    purchased_credit_balance_zero: bool | None = None
    auto_reload_enabled: bool | None = None
    active_work: bool | None = None
    inactivity_verified: bool = False


class StatusAdapter(Protocol):
    """Must verify account identity, actual buckets and model availability read-only.

    None means unavailable, never unused. Never fill missing fields with zeros.
    Implementations must not initiate model turns or redeem earned-reset credits.
    """
    def read(self, account_id: str) -> Status | None: ...


@dataclass(frozen=True)
class Event:
    event_id: str
    kind: str  # global_reset, banked_grant, ordinary_expiration
    occurred_at: float
    source: str
    confirmed: bool | None = None
    announcement_state: str = "unknown"


@dataclass(frozen=True)
class Profile:
    account_id: str
    plan_label: str
    assumed_windows_minutes: tuple[int, ...]
    assumptions_verified: bool = False
    model_id: str | None = None
    subscription_auth_verified: bool = False
    model_verified: bool = False
    usage_impact_verified: bool = False
    reset_behavior_verified: bool = False
    paid_fallback_prevented_verified: bool = False
    activity_policy: str = "verified_inactivity"
    trigger_window_minutes: int | None = None


@dataclass(frozen=True)
class Policy:
    status_max_age_seconds: int = 300
    safety_margin_seconds: int = 60
    unknown_recheck_seconds: int = 3600
    retry_delay_seconds: int = 60
    fixed_reset_min_read_gap_seconds: int = 60
    reset_tolerance_seconds: int = 180


@dataclass(frozen=True)
class Decision:
    account_id: str
    action: str
    reason: str
    next_check_at: float
    opportunity_id: str | None = None
    trigger_at: float | None = None
    window_key: str | None = None
    window_minutes: int | None = None
    valid_until: float | None = None


def valid_status(profile, status, now, policy=Policy()):
    """Validate complete normalized snapshots without converting unknowns to zero."""
    if (status is None or status.account_id != profile.account_id or status.verified is not True
            or status.ordinary_usage_allowed is not True):
        return False
    if (type(status.observed_at) not in (int, float) or not math.isfinite(status.observed_at)
            or not 0 <= now - status.observed_at <= policy.status_max_age_seconds):
        return False
    if not status.windows or len(status.windows) > 16 or len({w.key for w in status.windows}) != len(status.windows):
        return False
    if (not profile.assumed_windows_minutes
            or any(type(v) is not int or v <= 0 for v in profile.assumed_windows_minutes)
            or not set(profile.assumed_windows_minutes).issubset({w.duration_minutes for w in status.windows})):
        return False
    return all(isinstance(w.key, str) and 0 < len(w.key) <= 100
               and type(w.used_percent) in (int, float) and math.isfinite(w.used_percent)
               and 0 <= w.used_percent <= 100 and type(w.duration_minutes) is int
               and w.duration_minutes > 0 and type(w.resets_at) in (int, float)
               and math.isfinite(w.resets_at) and 0 < w.resets_at < 32503680000
               for w in status.windows)


def fixed_record_valid(record, duration=None):
    if not isinstance(record, dict):
        return False
    values = [record.get(k) for k in ("resets_at", "first_observed_at", "verified_at")]
    return (all(type(v) in (int, float) and math.isfinite(v) and 0 < v < 32503680000 for v in values)
            and values[1] < values[2] < values[0]
            and type(record.get("duration_minutes")) is int and record["duration_minutes"] > 0
            and (duration is None or record["duration_minutes"] == duration))


def observe_fixed_resets(profile, status, state, now, policy=Policy()):
    """Two fresh distinct reads establish a fixed timer, never a drifting idle clock.

    Keep the last verified anchor when an idle endpoint advances now + duration.
    Persist this state under the same exclusive lock as decisions and dispatch.
    Legacy previous snapshots are intentionally not promoted into fixed anchors.
    """
    if not valid_status(profile, status, now, policy):
        return
    anchors = state.setdefault("fixed_resets", {})
    candidates = state.setdefault("reset_candidates", {})
    for w in status.windows:
        if w.resets_at <= now:
            continue
        prior = candidates.get(w.key, {})
        if (prior.get("resets_at") != w.resets_at or prior.get("duration_minutes") != w.duration_minutes
                or status.observed_at < prior.get("first_observed_at", float("inf"))):
            candidates[w.key] = {"resets_at": w.resets_at, "duration_minutes": w.duration_minutes,
                                 "first_observed_at": status.observed_at}
            continue
        if status.observed_at - prior["first_observed_at"] < policy.fixed_reset_min_read_gap_seconds:
            continue
        record = {**prior, "verified_at": status.observed_at}
        old = anchors.get(w.key)
        if fixed_record_valid(record, w.duration_minutes) and (not fixed_record_valid(old) or w.resets_at >= old["resets_at"]):
            anchors[w.key] = record
    # Never silently evict durable dedup/anchor entries to make room.
    if len(anchors) > 16 or len(candidates) > 16:
        raise ValueError("Window identity changed; inspect state before continuing")


def decide(profile, status, previous, events, state, now, policy=Policy()):
    """Dry-run decision from fixed-reset evidence, with an explicit activity policy.

    previous is retained for API compatibility, but a single prior snapshot is
    not fixed-timer evidence. Percentages are a heuristic, not inactivity proof.
    """
    fallback = now + policy.unknown_recheck_seconds
    def hold(reason, next_at=fallback):
        return Decision(profile.account_id, "hold", reason, next_at)
    if state.get("inflight") or state.get("uncertain"):
        return hold("Previous request outcome is uncertain; reconcile manually")
    cleanup = state.get("completed_disposable")
    if cleanup and cleanup.get("cleanup") != "archived":
        return hold("Previous disposable chat cleanup pending; reconcile before another request")
    if status is None:
        return hold("Account status unavailable")
    if status.account_id != profile.account_id or status.verified is not True:
        return hold("Account identity/status provenance unverified")
    if status.ordinary_usage_allowed is not True:
        return hold("Ordinary subscription usage permission unavailable or denied")
    if not valid_status(profile, status, now, policy):
        return hold("Status stale, incomplete or invalid")
    if profile.activity_policy not in {"verified_inactivity", "remaining_percent_heuristic"}:
        return hold("Unknown activity policy")
    target_minutes = profile.trigger_window_minutes
    if target_minutes is not None and (type(target_minutes) is not int or target_minutes <= 0):
        return hold("Invalid trigger window")
    if profile.activity_policy == "remaining_percent_heuristic" and target_minutes is None:
        return hold("Heuristic requires an explicit trigger window duration")
    if target_minutes is not None and target_minutes not in profile.assumed_windows_minutes:
        return hold("Trigger window is missing from verified coverage")
    if profile.activity_policy == "remaining_percent_heuristic" and target_minutes == 300 and 10080 not in profile.assumed_windows_minutes:
        return hold("Five-hour heuristic requires weekly bucket coverage")
    targets = [w for w in status.windows if target_minutes is None or w.duration_minutes == target_minutes]
    if not targets or (target_minutes is not None and len(targets) != 1):
        return hold("Configured trigger window unavailable or ambiguous")
    if any(w.resets_at <= now for w in status.windows):
        return Decision(profile.account_id, "check_status", "Reset time passed; obtain refreshed buckets",
                        now + policy.safety_margin_seconds)
    deadlines = [w.resets_at + policy.safety_margin_seconds for w in status.windows]
    for w in targets:
        anchor = state.get("fixed_resets", {}).get(w.key)
        if fixed_record_valid(anchor, w.duration_minutes):
            deadline = anchor["resets_at"] + policy.safety_margin_seconds
            if deadline > now:
                deadlines.append(deadline)
        candidate = state.get("reset_candidates", {}).get(w.key, {})
        if (candidate.get("resets_at") == w.resets_at
                and candidate.get("duration_minutes") == w.duration_minutes
                and type(candidate.get("first_observed_at")) in (int, float)
                and (not fixed_record_valid(anchor, w.duration_minutes) or anchor["resets_at"] != w.resets_at)):
            confirmation_at = candidate["first_observed_at"] + policy.fixed_reset_min_read_gap_seconds
            deadlines.append(max(now + policy.safety_margin_seconds, confirmation_at))
    next_at = min(deadlines)
    if any(w.used_percent >= 100 for w in status.windows):
        return hold("A usage bucket is exhausted", next_at)
    for event in events:
        if (event.kind == "global_reset" and event.occurred_at <= now
                and status.observed_at < event.occurred_at + policy.safety_margin_seconds):
            return Decision(profile.account_id, "check_status", "Public reset hint; personal refill unverified",
                            max(now + policy.safety_margin_seconds, event.occurred_at + policy.safety_margin_seconds))
    triggers = []
    for w in targets:
        anchor = state.get("fixed_resets", {}).get(w.key)
        if not fixed_record_valid(anchor, w.duration_minutes):
            continue
        trigger = anchor["resets_at"]
        if (trigger + policy.safety_margin_seconds <= now
                and status.observed_at >= trigger + policy.safety_margin_seconds
                and w.resets_at > trigger
                and trigger > state.get("handled_windows", {}).get(w.key, 0)
                and trigger > state.get("handled_through", 0)):
            triggers.append((trigger, w))
    if not triggers:
        return hold("No expired verified fixed-reset opportunity", next_at)
    trigger, target = max(triggers, key=lambda pair: (pair[0], pair[1].key))
    usage_windows = targets if profile.activity_policy == "remaining_percent_heuristic" else status.windows
    if any(w.used_percent != 0 for w in usage_windows):
        return hold("Target usage already active; skip disposable request", next_at)
    gates = (profile.assumptions_verified, profile.subscription_auth_verified,
             profile.model_verified, profile.usage_impact_verified, profile.reset_behavior_verified,
             profile.paid_fallback_prevented_verified)
    if not all(flag is True for flag in gates):
        return hold("Authentication, model, usage/reset behavior, bucket coverage or paid-credit prevention unverified", next_at)
    if not profile.model_id or profile.model_id not in status.model_ids:
        return hold("Configured model unavailable in account model list", next_at)
    if status.purchased_credit_balance_zero is not True or status.auto_reload_enabled is not False:
        return hold("Zero purchased credits and disabled auto reload unverified", next_at)
    if status.active_work is True:
        return hold("Active work reported; skip disposable request", next_at)
    if profile.activity_policy == "verified_inactivity" and (status.active_work is not False or not status.inactivity_verified):
        return hold("Cross-device inactivity unverified; rounded percentages are insufficient", next_at)
    opportunity = hashlib.sha256(f"{profile.account_id}:{target.key}:{trigger}".encode()).hexdigest()
    attempt = state.get("attempt")
    if attempt and attempt["id"] == opportunity:
        if attempt["outcome"] in {"success", "hold", "uncertain"}:
            return hold("Opportunity already handled", next_at)
        if attempt["count"] >= 2:
            return hold("One retry used; hold for this opportunity", next_at)
        if now < attempt["retry_at"]:
            return hold("Bounded retry not yet due", attempt["retry_at"])
    reason = ("100% remaining heuristic after fixed reset; inactivity is not proven"
              if profile.activity_policy == "remaining_percent_heuristic"
              else "Verified unused buckets after fixed reset")
    return Decision(profile.account_id, "would_request", reason, next_at,
                    opportunity, trigger, target.key, target.duration_minutes,
                    status.observed_at + policy.status_max_age_seconds)
