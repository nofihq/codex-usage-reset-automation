"""Pure decisions. No I/O, model calls, inferred grants or credential access."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
import hashlib


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


@dataclass(frozen=True)
class Policy:
    status_max_age_seconds: int = 300
    safety_margin_seconds: int = 60
    unknown_recheck_seconds: int = 3600
    retry_delay_seconds: int = 60


@dataclass(frozen=True)
class Decision:
    account_id: str
    action: str
    reason: str
    next_check_at: float
    opportunity_id: str | None = None
    trigger_at: float | None = None


def decide(profile, status, previous, events, state, now, policy=Policy()):
    """Observed expiration/reset is a candidate; unknown or unverified means hold.

    No request happens here. Actual bucket times override plan assumptions.
    Feed events only request status refresh, never establish personal reset.
    """
    fallback = now + policy.unknown_recheck_seconds
    def hold(reason, next_at=fallback):
        return Decision(profile.account_id, "hold", reason, next_at)
    if state.get("inflight") or state.get("uncertain"):
        return hold("Previous request outcome is uncertain; reconcile manually")
    if status is None:
        return hold("Account status unavailable")
    if status.account_id != profile.account_id or not status.verified:
        return hold("Account identity/status provenance unverified")
    if status.ordinary_usage_allowed is not True:
        return hold("Ordinary subscription usage permission unavailable or denied")
    if not 0 <= now - status.observed_at <= policy.status_max_age_seconds:
        return hold("Account status stale or from the future")
    if not status.windows or len({w.key for w in status.windows}) != len(status.windows):
        return hold("Complete distinct rate-limit buckets unavailable")
    if any(not 0 <= w.used_percent <= 100 or w.duration_minutes <= 0 for w in status.windows):
        return hold("Invalid rate-limit values")
    due = [w.resets_at + policy.safety_margin_seconds for w in status.windows]
    if any(w.resets_at <= now for w in status.windows):
        return Decision(profile.account_id, "check_status", "Reset time passed; obtain refreshed buckets",
                        now + policy.safety_margin_seconds)
    next_at = min(due)
    if any(w.used_percent >= 100 for w in status.windows):
        return hold("A usage bucket is exhausted", next_at)
    triggers = []
    for event in events:
        if (event.kind == "global_reset" and event.occurred_at <= now
                and status.observed_at < event.occurred_at + policy.safety_margin_seconds):
            return Decision(profile.account_id, "check_status", "Public reset hint; personal refill unverified",
                            max(now + policy.safety_margin_seconds, event.occurred_at + policy.safety_margin_seconds))
    if previous:
        old = {w["key"]: w for w in previous.get("windows", [])}
        for w in status.windows:
            prior = old.get(w.key)
            if (prior and prior["resets_at"] + policy.safety_margin_seconds <= now
                    and status.observed_at >= prior["resets_at"] + policy.safety_margin_seconds
                    and w.resets_at > prior["resets_at"]):
                triggers.append(prior["resets_at"])
    triggers = [t for t in triggers if t > state.get("handled_through", 0)]
    if not triggers:
        return hold("No new corroborated reset/expiration opportunity", next_at)
    trigger = max(triggers)
    if any(w.used_percent != 0 for w in status.windows):
        return hold("Usage already active; skip disposable request", next_at)
    gates = (profile.assumptions_verified, profile.subscription_auth_verified,
             profile.model_verified, profile.usage_impact_verified, profile.reset_behavior_verified,
             profile.paid_fallback_prevented_verified)
    if not all(gates):
        return hold("Authentication, model, usage/reset behavior, bucket coverage or paid-credit prevention unverified", next_at)
    if not profile.model_id or profile.model_id not in status.model_ids:
        return hold("Configured model unavailable in account model list", next_at)
    if status.purchased_credit_balance_zero is not True or status.auto_reload_enabled is not False:
        return hold("Zero purchased credits and disabled auto reload unverified", next_at)
    if status.active_work is not False or not status.inactivity_verified:
        return hold("Cross-device inactivity unverified; rounded percentages are insufficient", next_at)
    opportunity = hashlib.sha256(f"{profile.account_id}:{trigger}".encode()).hexdigest()
    attempt = state.get("attempt")
    if attempt and attempt["id"] == opportunity:
        if attempt["outcome"] in {"success", "hold", "uncertain"}:
            return hold("Opportunity already handled", next_at)
        if attempt["count"] >= 2:
            return hold("One retry used; hold for this opportunity", next_at)
        if now < attempt["retry_at"]:
            return hold("Bounded retry not yet due", attempt["retry_at"])
    return Decision(profile.account_id, "would_request", "Verified unused buckets after reset/expiration",
                    next_at, opportunity, trigger)
