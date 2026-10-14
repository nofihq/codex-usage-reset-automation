"""Disabled disposable OK-only adapter; no subprocess, HTTP or API fallback."""
from dataclasses import dataclass
from typing import Protocol

PROMPT = "Reply with exactly OK. Do not use tools or perform any other work."


@dataclass(frozen=True)
class RequestResult:
    outcome: str  # success, safe_retry (proven no usage), hold, uncertain


class RequestAdapter(Protocol):
    enabled: bool
    def request(self, account_id: str, model_id: str, prompt: str, key: str) -> RequestResult: ...


class DisabledRequestAdapter:
    enabled = False
    def request(self, *args, **kwargs):
        raise RuntimeError("Live OK-only requests are disabled in this MVP")


def dispatch(decision, profile, adapter, account_state, now, save, dry_run=True, retry_delay=60):
    """Fixture-testable transaction envelope; CLI never enables live execution.

    One retry only after a verified no-usage failure. Exceptions/timeouts/crashes
    are uncertain and never automatically retried. Inflight is saved BEFORE call.
    Exactly-once model execution cannot be promised without upstream idempotency.
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
    if not all(gates) or not profile.model_id:
        return "disabled"
    if account_state.get("inflight") or account_state.get("uncertain"):
        return "uncertain"
    if decision.trigger_at <= account_state.get("handled_through", 0):
        return "duplicate"
    attempt = account_state.get("attempt", {})
    count = attempt.get("count", 0) if attempt.get("id") == decision.opportunity_id else 0
    if count >= 2 or (count and now < attempt.get("retry_at", float("inf"))):
        return "hold"
    account_state["inflight"] = decision.opportunity_id
    save()
    try:
        result = adapter.request(profile.account_id, profile.model_id, PROMPT, decision.opportunity_id)
        outcome = result.outcome if result.outcome in {"success", "safe_retry", "hold", "uncertain"} else "uncertain"
    except Exception:
        outcome = "uncertain"
    count += 1
    if outcome == "safe_retry" and count >= 2:
        outcome = "hold"
    account_state["attempt"] = {"id": decision.opportunity_id, "count": count,
                                "outcome": outcome, "retry_at": now + max(60, retry_delay)}
    account_state.pop("inflight", None)
    if outcome != "safe_retry":
        account_state["handled_through"] = decision.trigger_at
    if outcome == "uncertain":
        account_state["uncertain"] = True
    save()
    return outcome
