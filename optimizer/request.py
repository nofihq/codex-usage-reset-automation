"""Disabled request/cleanup adapters and a fixture-testable safety envelope.

There is no CLI or browser dispatcher here. Implementing these Protocols does
not constitute verification of a provider, model, billing behavior or runtime.
"""
from dataclasses import dataclass
import hashlib
import time
from typing import Protocol

from .core import Policy, Status, valid_status, fixed_record_valid

PROMPT = "Reply with exactly OK. Do not use tools or perform any other work."


@dataclass(frozen=True)
class RequestResult:
    outcome: str  # success, safe_retry (proven no usage), hold, uncertain
    completed: bool = False
    response_text: str | None = None
    account_id: str | None = None
    model_id: str | None = None
    thread_id: str | None = None
    disposable: bool = False
    requested_at: float | None = None
    completed_at: float | None = None
    status_reads: tuple[Status, ...] = ()
    no_usage_verified: bool = False


class RequestAdapter(Protocol):
    enabled: bool
    def request(self, account_id: str, model_id: str, prompt: str, key: str) -> RequestResult: ...


class DisabledRequestAdapter:
    enabled = False
    def request(self, *args, **kwargs):
        raise RuntimeError("Live OK-only requests are disabled in this MVP")


def verify_completed_request(decision, profile, result, sent_at, now, policy=Policy()):
    """Return a fixed-reset record only for exact OK plus two corroborating reads.

    Tiny requests can still display 100% remaining. Usage percentage changes are
    neither required nor sufficient. A claimed success without evidence is
    uncertain, and cannot be retried automatically.
    """
    if (not isinstance(result, RequestResult) or result.outcome != "success"
            or result.completed is not True or result.response_text != "OK"
            or result.disposable is not True or result.account_id != profile.account_id
            or result.model_id != profile.model_id
            or not isinstance(result.thread_id, str) or not 0 < len(result.thread_id) <= 200
            or any(c.isspace() or ord(c) < 32 for c in result.thread_id)
            or type(result.requested_at) not in (float, int)
            or type(result.completed_at) not in (float, int)
            or not sent_at <= result.requested_at <= result.completed_at <= now
            or result.requested_at - sent_at > policy.status_max_age_seconds
            or type(decision.window_minutes) is not int or decision.window_minutes <= 0
            or len(result.status_reads) != 2):
        return None
    first, second = result.status_reads
    if (not valid_status(profile, first, now, policy) or not valid_status(profile, second, now, policy)
            or first.observed_at < result.completed_at
            or second.observed_at - first.observed_at < policy.fixed_reset_min_read_gap_seconds):
        return None
    windows = []
    for status in (first, second):
        if (status.purchased_credit_balance_zero is not True or status.auto_reload_enabled is not False
                or any(w.used_percent >= 100 or w.resets_at <= now for w in status.windows)
                or status.active_work is True or profile.model_id not in status.model_ids):
            return None
        matching = [w for w in status.windows if w.key == decision.window_key
                    and w.duration_minutes == decision.window_minutes]
        if len(matching) != 1:
            return None
        windows.append(matching[0])
    before, after = windows
    expected = result.requested_at + decision.window_minutes * 60
    if (before.resets_at != after.resets_at or after.resets_at <= now
            or abs(after.resets_at - expected) > policy.reset_tolerance_seconds):
        return None
    return {"resets_at": after.resets_at, "duration_minutes": after.duration_minutes,
            "first_observed_at": first.observed_at, "verified_at": second.observed_at}


def dispatch(decision, profile, adapter, account_state, now, save, dry_run=True,
             retry_delay=60, policy=Policy(), clock=time.time):
    """Transaction envelope; caller holds the Store lock across the entire call.

    save must atomically fsync private durable state. Inflight is saved BEFORE
    any external call. A save failure prevents sending; a crash/timeout leaves
    an unresolved marker. Exactly-once execution requires upstream idempotency
    and is not promised here. No real adapter is shipped or enabled by the CLI.
    """
    if decision.action != "would_request":
        return "hold"
    if dry_run:
        return "dry_run"
    if not adapter.enabled:
        return "disabled"
    gates = (profile.assumptions_verified, profile.subscription_auth_verified,
             profile.model_verified, profile.usage_impact_verified, profile.reset_behavior_verified,
             profile.paid_fallback_prevented_verified)
    if not all(flag is True for flag in gates) or not profile.model_id:
        return "disabled"
    if (decision.account_id != profile.account_id or decision.trigger_at is None
            or not decision.window_key or not decision.window_minutes
            or decision.valid_until is None or now > decision.valid_until):
        return "hold"
    expected_key = hashlib.sha256(f"{profile.account_id}:{decision.window_key}:{decision.trigger_at}".encode()).hexdigest()
    if decision.opportunity_id != expected_key:
        return "hold"
    if account_state.get("inflight") or account_state.get("uncertain"):
        return "uncertain"
    if (decision.trigger_at <= account_state.get("handled_through", 0)
            or decision.trigger_at <= account_state.get("handled_windows", {}).get(decision.window_key, 0)):
        return "duplicate"
    cleanup = account_state.get("completed_disposable")
    if cleanup and cleanup.get("cleanup") != "archived":
        return "hold"
    anchor = account_state.get("fixed_resets", {}).get(decision.window_key)
    if (not fixed_record_valid(anchor, decision.window_minutes)
            or anchor["resets_at"] != decision.trigger_at
            or decision.trigger_at + policy.safety_margin_seconds > now):
        return "hold"
    attempt = account_state.get("attempt", {})
    same_attempt = attempt.get("id") == decision.opportunity_id
    if same_attempt and attempt.get("outcome") != "safe_retry":
        return "duplicate"
    count = attempt.get("count", 0) if same_attempt else 0
    if count >= 2 or (count and now < attempt.get("retry_at", float("inf"))):
        return "hold"
    account_state["inflight"] = {"id": decision.opportunity_id, "window_key": decision.window_key,
                                  "trigger_at": decision.trigger_at, "started_at": now}
    save()
    # Disk I/O can stall. Do not send using a decision that expired while saving.
    sent_at = clock()
    if not now <= sent_at <= decision.valid_until:
        account_state.pop("inflight", None)
        save()
        return "hold"
    fixed = None
    try:
        result = adapter.request(profile.account_id, profile.model_id, PROMPT, decision.opportunity_id)
        outcome = result.outcome if isinstance(result, RequestResult) and result.outcome in {"success", "safe_retry", "hold", "uncertain"} else "uncertain"
        if outcome == "success":
            fixed = verify_completed_request(decision, profile, result, sent_at, clock(), policy)
            if fixed is None:
                outcome = "uncertain"
        elif outcome == "safe_retry" and result.no_usage_verified is not True:
            outcome = "uncertain"
    except Exception:
        outcome = "uncertain"
    count += 1
    if outcome == "safe_retry" and count >= 2:
        outcome = "hold"
    account_state["attempt"] = {"id": decision.opportunity_id, "count": count,
                                "outcome": outcome, "retry_at": now + max(60, retry_delay)}
    account_state.pop("inflight", None)
    if outcome != "safe_retry":
        account_state.setdefault("handled_windows", {})[decision.window_key] = decision.trigger_at
    if outcome == "uncertain":
        account_state["uncertain"] = True
    if outcome == "success":
        account_state.setdefault("fixed_resets", {})[decision.window_key] = fixed
        account_state["completed_disposable"] = {
            "thread_id": result.thread_id, "account_id": profile.account_id,
            "model_id": profile.model_id, "completed_at": result.completed_at,
            "opportunity_id": decision.opportunity_id, "verified": True,
            "cleanup": "pending"}
    save()
    return outcome


@dataclass(frozen=True)
class ThreadStatus:
    thread_id: str
    account_id: str
    completed: bool
    archived: bool
    disposable: bool


class ArchiveAdapter(Protocol):
    enabled: bool
    def read_thread(self, account_id: str, thread_id: str) -> ThreadStatus: ...
    def archive(self, account_id: str, thread_id: str) -> None: ...


class DisabledArchiveAdapter:
    enabled = False
    def read_thread(self, *args, **kwargs):
        raise RuntimeError("Live cleanup is disabled")
    def archive(self, *args, **kwargs):
        raise RuntimeError("Live cleanup is disabled")


def archive_completed_disposable(profile, adapter, account_state, save, dry_run=True):
    """Archive only the exact proven completed disposable chat; never delete.

    Archive is retention, not deletion. Unknown outcomes are reconciled by a
    read on a later call; an uncertain archive is not repeated automatically.
    Caller holds the same exclusive state lock as dispatch.
    """
    if dry_run:
        return "dry_run"
    if not adapter.enabled:
        return "disabled"
    record = account_state.get("completed_disposable", {})
    if (record.get("verified") is not True or record.get("account_id") != profile.account_id
            or not record.get("thread_id") or not record.get("opportunity_id")):
        return "hold"
    if record.get("cleanup") == "archived":
        return "archived"
    def matches(observed):
        return (isinstance(observed, ThreadStatus) and observed.thread_id == record["thread_id"]
                and observed.account_id == profile.account_id and observed.completed is True
                and observed.disposable is True and type(observed.archived) is bool)
    try:
        before = adapter.read_thread(profile.account_id, record["thread_id"])
        if not matches(before):
            return "hold"
        if before.archived:
            record["cleanup"] = "archived"
            save()
            return "archived"
        if record.get("cleanup") != "pending":
            return "uncertain"
        record["cleanup"] = "inflight"
        save()
        adapter.archive(profile.account_id, record["thread_id"])
        after = adapter.read_thread(profile.account_id, record["thread_id"])
        outcome = "archived" if matches(after) and after.archived else "uncertain"
    except Exception:
        outcome = "uncertain"
    record["cleanup"] = outcome
    save()
    return outcome
