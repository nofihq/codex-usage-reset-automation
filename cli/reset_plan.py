"""Compute read-only decisions for Dot. No network, credentials, or writes."""
import hashlib
import json
import sys
from datetime import datetime

HOUR = 3600
DAY = 24 * HOUR
TARGETS = (300, 10080)
MAX_TIME = 253402300799
MAX_INPUT = 65536


def stamp(value):
    if type(value) is not int or not 0 <= value <= MAX_TIME:
        raise ValueError("invalid_timestamp")
    return value


def metadata(result, target):
    if (target not in TARGETS or type(target) is not int
            or result.get("state") != "metadata_verified"
            or result.get("identityMatchesExpected") is not True
            or result.get("usageBindingMatchesExpected") is not True):
        raise ValueError("unverified_metadata_or_target")
    usage = result["usage"]
    # Named Codex data is authoritative. Use the legacy snapshot only if absent.
    bucket = usage["rateLimitsByLimitId"]["codex"]
    if bucket is None:
        bucket = usage["rateLimits"]
    windows = [bucket.get(k) for k in ("primary", "secondary")]
    windows = [w for w in windows if w is not None]
    selected = [w for w in windows if w.get("windowDurationMins") == target]
    if len(selected) != 1:
        raise ValueError("ambiguous_or_missing_target")
    reset = stamp(selected[0]["resetsAt"])
    percentages = [w["usedPercent"] for w in windows]
    if any(type(p) not in (int, float) or not 0 <= p <= 100 for p in percentages):
        raise ValueError("unknown_usage")
    return usage, selected[0], reset, percentages


def observation(result, target):
    usage, window, reset, percentages = metadata(result, target)
    return {
        "resets_at": reset,
        "remaining_percent": 100 - window["usedPercent"],
        "passes_usage_gate": (usage.get("ordinaryUsageAllowed") is True
                              and window["usedPercent"] == 0 and max(percentages) < 100),
    }


def verify_window(first, second, target, sent_at, completed_at):
    sent_at, completed_at = stamp(sent_at), stamp(completed_at)

    def captured_at(result):
        value = datetime.fromisoformat(result["checkedAt"].replace("Z", "+00:00"))
        if value.tzinfo is None:
            raise ValueError("missing_capture_timezone")
        return value.timestamp()

    a = observation(first, target)["resets_at"]
    b = observation(second, target)["resets_at"]
    t1, t2 = captured_at(first), captured_at(second)
    start = b - target * 60
    # Reader timestamps have fractions; server and send bounds use Unix seconds.
    if not (sent_at <= start <= completed_at <= t1 and t2 - t1 >= 60 and a == b and t2 < b):
        raise ValueError("fixed_window_unverified")
    return {"resets_at": b, "normal_due_at": stamp(b + 120)}


def route_wake(now, intended_at, delivery, mode, ledger, has_hold):
    """Return the account scope and whether the coordinator can check saved reminders."""
    now, intended_at = stamp(now), stamp(intended_at)
    if (delivery not in ("intended", "recurrence", "unknown")
            or mode not in ("ordinary", "reminder", "recovery", "state")
            or ledger not in ("fresh", "temporary_error", "unavailable")
            or type(has_hold) is not bool):
        raise ValueError("invalid_wake")
    if ledger != "fresh":
        return {"scope": "service_only", "reason": ledger, "check_saved_reminders": False}
    if delivery == "unknown" or now < intended_at:
        return {"scope": "service_only", "reason": "unverified_or_early_wake",
                "check_saved_reminders": False}
    if delivery == "recurrence":
        return {"scope": "service_only", "reason": "fallback_wake", "check_saved_reminders": True}
    if mode == "reminder":
        return {"scope": "saved_reminders_only", "check_saved_reminders": True}
    if mode == "state" or has_hold:
        return {"scope": "service_only", "reason": "state_wake_or_hold", "check_saved_reminders": True}
    if mode == "recovery":
        return {"scope": "eligibility_read_only", "check_saved_reminders": True}
    # After an outage, a sparse fallback can land many hours later. It must
    # never be interpreted as catch-up authorization for the ordinary run.
    if now - intended_at > HOUR:
        return {"scope": "service_only", "reason": "stale_ordinary_wake", "check_saved_reminders": True}
    return {"scope": "ordinary_preflight", "check_saved_reminders": True}


def plan_public_notice(kind, message_id, event_id, authenticated, native, receipts):
    """Deduplicate a classified source event independently of account state."""
    if native is not True or authenticated is not True:
        return {"scope": "hold_unverified_source"}
    if kind == "subscription":
        return {"scope": "ignore"}
    if kind not in ("forecast", "global", "banked"):
        return {"scope": "hold_unclassified_source"}

    def key(prefix, value):
        if not isinstance(value, str) or not value.strip() or len(value) > 1024:
            raise ValueError("invalid_source_id")
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return f"{prefix}:{digest}"

    keys = [key("message", message_id)]
    if event_id is not None:
        keys.append(key(kind, event_id))
    states = [receipts.get(k) for k in keys]
    if any(state not in (None, "claimed", "accepted", "unknown") for state in states):
        raise ValueError("invalid_public_receipt")
    if "accepted" in states:
        return {"scope": "duplicate"}
    if any(state is not None for state in states):
        return {"scope": "reconcile_only"}
    return {"scope": "claim_public_notice", "keys": keys, "kind": kind}


def reminder_plan(now, normal_due_at, inventory, receipts, retry_at=None):
    """Plan current-account notices; receipts are keyed by expiry/grant time/ordinal/stage.

    inventory is the sanitized banked inventory from a fresh authorized reader
    result, or the latest saved copy. Callers must preserve receipts on refresh.
    A claimed, accepted, or unknown receipt blocks automatic repeat delivery.
    """
    now = stamp(now)
    normal_due_at = stamp(normal_due_at)
    wake = [normal_due_at] if normal_due_at > now else []
    if retry_at is not None:
        retry_at = stamp(retry_at)
        if retry_at <= now:
            raise ValueError("retry_not_in_future")
        wake.append(retry_at)
    due, reconcile = [], []
    grants = {}
    rows = None if inventory is None else inventory.get("credits")
    if rows is not None and not isinstance(rows, list):
        raise ValueError("invalid_inventory_rows")
    unknown = rows is None
    count = None if inventory is None else inventory.get("availableCount")
    if count is not None and (type(count) is not int or count < 0):
        raise ValueError("invalid_inventory_count")
    available_rows = 0
    for row in rows or ():
        if row.get("status") != "available":
            unknown |= row.get("status") in (None, "unknown")
            continue
        available_rows += 1
        if row.get("expiresAt") is None or row.get("grantedAt") is None:
            unknown = True
            continue
        grant, expiry = stamp(row["grantedAt"]), stamp(row["expiresAt"])
        if expiry <= grant:
            raise ValueError("invalid_grant_interval")
        if expiry > now:
            grants[expiry, grant] = grants.get((expiry, grant), 0) + 1
    # A partial snapshot may still give exact warnings for known grants.
    unknown |= count is None or available_rows != count
    if any(status not in ("claimed", "accepted", "unknown", "suppressed")
           for status in receipts.values()):
        raise ValueError("invalid_reminder_receipt")
    for (expiry, grant), quantity in sorted(grants.items()):
        for i in range(1, quantity + 1):
            prefix = f"{expiry}:{grant}:{i}:"
            pending = []
            uncertain = False
            for hours in (72, 24):
                key, deadline = prefix + str(hours), expiry - hours * HOUR
                status = receipts.get(key)
                if status in ("unknown", "claimed"):
                    reconcile.append(key)
                    uncertain = True
                elif status is None:
                    pending.append((key, deadline))
            # A later stage must not turn an unknown first send into a blind retry.
            if uncertain:
                continue
            for _, deadline in pending:
                if deadline > now:
                    wake.append(deadline)
            stages = [key for key, deadline in pending if deadline <= now]
            if stages:
                due.append({"expires_at": expiry, "stages": stages,
                            "late_first_notice": expiry - now < DAY
                            and receipts.get(prefix + "72") != "accepted"})
    return {"normal_due": normal_due_at <= now, "due_notices": due,
            "reconcile": reconcile, "inventory_incomplete": unknown,
            "next_future_wake": min(wake, default=None)}


OPERATIONS = {"observe": observation, "verify_window": verify_window, "route_wake": route_wake,
              "plan_public_notice": plan_public_notice,
              "plan_reminders": reminder_plan}


def unique_keys(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("duplicate_json_keys")
    return result


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            raise ValueError("input_too_large")
        payload = json.loads(raw, object_pairs_hook=unique_keys)
        operation = OPERATIONS[payload.pop("operation")]
        result = operation(**payload)
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError, OSError, RecursionError):
        # Never echo input, which may contain private state.
        print('{"state":"hold","reason":"invalid_or_unverified_planner_input"}')
        return 2
    print(json.dumps({"state": "planned", **result}, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
