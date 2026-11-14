"""Regression checks for timing and fail-closed scope, without a Dot account."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import unittest

from cli import reset_plan as planner

NOW = 2_000_000_000
HOUR = planner.HOUR
DAY = planner.DAY


def status(capture, reset, target=300, target_used=0, other_used=25):
    return {
        "state": "metadata_verified",
        "identityMatchesExpected": True, "usageBindingMatchesExpected": True,
        "checkedAt": datetime.fromtimestamp(capture, timezone.utc).isoformat(),
        "usage": {"ordinaryUsageAllowed": True, "rateLimits": None,
                  "rateLimitsByLimitId": {"codex": {
                      "primary": {"windowDurationMins": 10080 if target == 300 else 300,
                                  "usedPercent": other_used, "resetsAt": reset},
                      "secondary": {"windowDurationMins": target,
                                    "usedPercent": target_used, "resetsAt": reset},
                  }}},
    }


def inventory(expiry, count=1):
    return {"availableCount": count, "credits": [
        {"status": "available", "grantedAt": expiry - 30 * DAY, "expiresAt": expiry}
        for _ in range(count)
    ]}


class WindowTiming(unittest.TestCase):
    def test_target_selected_by_duration_and_verified_for_both_windows(self):
        for target in (300, 10080):
            with self.subTest(target=target):
                reset = NOW + target * 60
                one = status(NOW + 3, reset, target)
                two = status(NOW + 63, reset, target)
                self.assertTrue(planner.observation(one, target)["passes_usage_gate"])
                self.assertEqual(planner.verify_window(one, two, target, NOW - 1, NOW + 2),
                                 {"resets_at": reset, "normal_due_at": reset + 120})

    def test_moving_stale_or_fast_pair_cannot_set_next_window(self):
        reset = NOW + 300 * 60
        for first_reset, second_reset, second_capture in (
                (reset, reset + 60, NOW + 63), (reset - 600, reset - 600, NOW + 63),
                (reset, reset, NOW + 62)):
            with self.subTest(first_reset=first_reset, second_reset=second_reset):
                with self.assertRaises(ValueError):
                    planner.verify_window(status(NOW + 3, first_reset),
                                          status(second_capture, second_reset),
                                          300, NOW, NOW + 2)

    def test_permission_and_other_bucket_exhaustion_stop_usage_gate(self):
        data = status(NOW, NOW + DAY, other_used=100)
        self.assertFalse(planner.observation(data, 300)["passes_usage_gate"])
        data = status(NOW, NOW + DAY)
        for permission in (None, False, 1):
            with self.subTest(permission=permission):
                data["usage"]["ordinaryUsageAllowed"] = permission
                self.assertFalse(planner.observation(data, 300)["passes_usage_gate"])

    def test_duplicate_target_or_unverified_identity_holds(self):
        data = status(NOW, NOW + DAY)
        data["usage"]["rateLimitsByLimitId"]["codex"]["primary"]["windowDurationMins"] = 300
        with self.assertRaises(ValueError):
            planner.observation(data, 300)
        data = status(NOW, NOW + DAY)
        data["usageBindingMatchesExpected"] = False
        with self.assertRaises(ValueError):
            planner.observation(data, 300)


class WakeScope(unittest.TestCase):
    def test_verified_fallback_can_check_reminders_under_an_account_hold(self):
        for delivery, ledger, now, expected in (
                ("recurrence", "fresh", NOW, True),
                ("intended", "fresh", NOW, True),
                ("unknown", "fresh", NOW, False),
                ("recurrence", "unavailable", NOW, False),
                ("recurrence", "fresh", NOW - 1, False)):
            with self.subTest(delivery=delivery, ledger=ledger, now=now):
                route = planner.route_wake(now, NOW, delivery, "state", ledger, True)
                self.assertEqual(route["scope"], "service_only")
                self.assertIs(route["check_saved_reminders"], expected)

    def test_actual_outage_and_fallback_cannot_send(self):
        for now, delivery, mode, ledger, hold in (
                (NOW, "intended", "ordinary", "temporary_error", False),
                (NOW, "intended", "ordinary", "unavailable", False),
                (NOW + 12 * HOUR, "recurrence", "ordinary", "fresh", False),
                (NOW + 12 * HOUR, "intended", "ordinary", "fresh", False),
                (NOW, "unknown", "ordinary", "fresh", False),
                (NOW - 1, "intended", "ordinary", "fresh", False),
                (NOW, "intended", "ordinary", "fresh", True),
                (NOW, "intended", "recovery", "fresh", True)):
            with self.subTest(delivery=delivery, ledger=ledger, now=now, hold=hold):
                self.assertEqual(planner.route_wake(now, NOW, delivery, mode, ledger, hold)["scope"],
                                 "service_only")

    def test_read_only_recovery_and_reminders_keep_distinct_scopes(self):
        for mode, hold, expected in (
                ("ordinary", False, "ordinary_preflight"),
                ("recovery", False, "eligibility_read_only"),
                ("reminder", True, "saved_reminders_only")):
            self.assertEqual(planner.route_wake(NOW, NOW, "intended", mode, "fresh", hold)["scope"],
                             expected)


class PublicNotice(unittest.TestCase):
    def test_forecast_does_not_swallow_confirmation_but_replay_does(self):
        decide = planner.plan_public_notice
        forecast = decide("forecast", "message-1", "event", True, True, {})
        self.assertEqual(forecast["scope"], "claim_public_notice")
        receipts = dict.fromkeys(forecast["keys"], "accepted")
        global_notice = decide("global", "message-2", "event", True, True, receipts)
        self.assertEqual(global_notice["scope"], "claim_public_notice")
        receipts.update(dict.fromkeys(global_notice["keys"], "accepted"))
        self.assertEqual(decide("global", "message-3", "event", True, True, receipts)["scope"],
                         "duplicate")

    def test_unverified_source_and_unknown_send_do_not_create_a_notice(self):
        decide = planner.plan_public_notice
        self.assertEqual(decide("banked", "message", None, True, False, {})["scope"],
                         "hold_unverified_source")
        keys = decide("banked", "message", None, True, True, {})["keys"]
        self.assertEqual(decide("banked", "message", None, True, True,
                                dict.fromkeys(keys, "unknown"))["scope"], "reconcile_only")


class Reminders(unittest.TestCase):
    def test_warning_does_not_move_normal_deadline_or_wait_behind_backoff(self):
        due = NOW + 6 * DAY
        snapshot = inventory(NOW + 4 * DAY)
        plan = planner.reminder_plan(NOW, due, snapshot, {}, retry_at=NOW + 2 * DAY)
        self.assertEqual(plan["next_future_wake"], NOW + DAY)
        self.assertFalse(plan["normal_due"])
        self.assertEqual(planner.reminder_plan(due, due, snapshot, {})["next_future_wake"], None)
        self.assertTrue(planner.reminder_plan(due, due, snapshot, {})["normal_due"])

    def test_first_notice_inside_72_hours_is_immediate(self):
        expiry = NOW + 2 * DAY
        plan = planner.reminder_plan(NOW, NOW + 5 * DAY, inventory(expiry), {})
        self.assertEqual(len(plan["due_notices"]), 1)
        self.assertFalse(plan["due_notices"][0]["late_first_notice"])
        self.assertEqual(len(plan["due_notices"][0]["stages"]), 1)
        self.assertEqual(plan["next_future_wake"], expiry - DAY)

    def test_late_discovery_groups_both_stages_and_preserves_multiplicity(self):
        snapshot = inventory(NOW + HOUR, 2)
        plan = planner.reminder_plan(NOW, NOW + DAY, snapshot, {})
        self.assertEqual(len(plan["due_notices"]), 2)
        self.assertTrue(all(row["late_first_notice"] for row in plan["due_notices"]))
        stages = [key for row in plan["due_notices"] for key in row["stages"]]
        self.assertEqual(len(set(stages)), 4)
        replay = planner.reminder_plan(NOW, NOW + DAY, snapshot,
                                       dict.fromkeys(stages, "accepted"))
        self.assertEqual(replay["due_notices"], [])

    def test_accepted_early_warning_allows_follow_up_unknown_delivery_holds(self):
        snapshot = inventory(NOW + 3 * DAY)
        early = planner.reminder_plan(NOW, NOW + DAY, snapshot, {})
        key, = early["due_notices"][0]["stages"]
        after = NOW + 2 * DAY
        accepted = planner.reminder_plan(after, after + DAY, snapshot, {key: "accepted"})
        self.assertEqual(len(accepted["due_notices"]), 1)
        self.assertFalse(accepted["due_notices"][0]["late_first_notice"])
        for state in ("claimed", "unknown"):
            blocked = planner.reminder_plan(after, after + DAY, snapshot, {key: state})
            self.assertEqual(blocked["due_notices"], [])
            self.assertEqual(blocked["reconcile"], [key])

    def test_missing_expiry_is_not_invented_and_expired_grants_are_quiet(self):
        snapshot = inventory(NOW, 2)
        snapshot["credits"][1]["expiresAt"] = None
        plan = planner.reminder_plan(NOW, NOW + DAY, snapshot, {})
        self.assertTrue(plan["inventory_incomplete"])
        self.assertEqual(plan["due_notices"], [])

    def test_cli_returns_redacted_hold_for_malformed_input(self):
        script = Path(planner.__file__)
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                                input='{"operation":"private-fixture-do-not-print"}', timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["state"], "hold")
        self.assertNotIn("private-fixture", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
