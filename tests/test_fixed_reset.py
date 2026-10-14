"""Synthetic lifecycle tests. No network, credentials, real chats or model calls."""
import contextlib
import copy
from dataclasses import asdict, replace
import io
import json
from pathlib import Path
import tempfile
import unittest

from optimizer.__main__ import load_config, main
from optimizer.core import Policy, Profile, Status, Window, decide, observe_fixed_resets, timestamp, iso
from optimizer.request import (DisabledArchiveAdapter, RequestResult, ThreadStatus,
                               archive_completed_disposable, dispatch, verify_completed_request)
from optimizer.storage import Store

NOW = timestamp("2026-10-14T12:02:00Z")
ROOT = Path(__file__).resolve().parents[1]


class Fixture:
    def setUp(self):
        self.profile = Profile("plus", "Plus", (300,10080), True, "fixture-model", True, True,
                               True, True, True, "remaining_percent_heuristic", 300)
        self.status = Status("plus", NOW, (Window("short",0,NOW+18000,300),
                                           Window("weekly",10,NOW+604800,10080)),
                             ("fixture-model",), True, True, True, False, None, False)
        self.state = {"fixed_resets": {"short": {"resets_at": NOW-120, "duration_minutes":300,
                                                 "first_observed_at":NOW-1000,"verified_at":NOW-900}}}

    def decision(self, status=None, state=None, profile=None, now=NOW):
        return decide(profile or self.profile, status or self.status, None, [],
                      self.state if state is None else state, now)

    def evidence(self):
        return RequestResult("success", True, "OK", "plus", "fixture-model", "fixture-disposable", True,
                             NOW, NOW+1, (replace(self.status,observed_at=NOW+2),
                                          replace(self.status,observed_at=NOW+62)))

    def send(self, result=None, state=None, save=lambda:None, now=NOW):
        result = result or self.evidence()
        class Fake:
            enabled=True
            def request(*args): return result
        return dispatch(self.decision(),self.profile,Fake(),self.state if state is None else state,
                        now,save,False,clock=iter((now,NOW+62)).__next__)

class Lifecycle(Fixture, unittest.TestCase):
    def test_opt_in_allows_unknown_inactivity_without_claiming_proof(self):
        decision = self.decision()
        self.assertEqual(decision.action,"would_request")
        self.assertIn("heuristic",decision.reason)
        self.assertIn("not proven",decision.reason)
        self.assertEqual(decision.window_minutes,300)

    def test_default_strict_still_requires_verified_inactivity(self):
        status=replace(self.status,windows=(self.status.windows[0],))
        strict=replace(self.profile,activity_policy="verified_inactivity",assumed_windows_minutes=(300,))
        self.assertEqual(self.decision(status=status,profile=strict).action,"hold")
        status=replace(status,active_work=False,inactivity_verified=True)
        self.assertEqual(self.decision(status=status,profile=strict).action,"would_request")

    def test_missing_weekly_status_cannot_pass_preflight_or_verification(self):
        status=replace(self.status,windows=(self.status.windows[0],))
        self.assertEqual(self.decision(status).action,"hold")
        result=self.evidence()
        result=replace(result,status_reads=tuple(replace(s,windows=(s.windows[0],)) for s in result.status_reads))
        self.assertIsNone(verify_completed_request(self.decision(),self.profile,result,NOW,NOW+62))

    def test_post_request_explicit_active_work_is_uncertain(self):
        result=self.evidence()
        result=replace(result,status_reads=(result.status_reads[0],replace(result.status_reads[1],active_work=True)))
        self.assertEqual(self.send(result),"uncertain")

    def test_target_not_plan_label_or_primary_order_selects_window(self):
        profile=replace(self.profile,plan_label="custom",trigger_window_minutes=10080)
        status=replace(self.status,windows=(replace(self.status.windows[1],used_percent=0),
                                           replace(self.status.windows[0],used_percent=20)))
        state={"fixed_resets":{"weekly":{"resets_at":NOW-120,"duration_minutes":10080,
                                           "first_observed_at":NOW-1000,"verified_at":NOW-900}}}
        self.assertEqual(self.decision(status,state,profile).window_key,"weekly")

    def test_target_nonzero_unknown_or_invalid_holds(self):
        for used in (0.1,1,100,None,float("nan"),True):
            with self.subTest(used=used):
                status=replace(self.status,windows=(replace(self.status.windows[0],used_percent=used),self.status.windows[1]))
                self.assertEqual(self.decision(status).action,"hold")

    def test_exhausted_or_unknown_other_bucket_holds(self):
        for used in (100,None):
            status=replace(self.status,windows=(self.status.windows[0],replace(self.status.windows[1],used_percent=used)))
            self.assertEqual(self.decision(status).action,"hold")

    def test_spending_identity_active_work_and_staleness_holds(self):
        for change in ({"purchased_credit_balance_zero":False},{"purchased_credit_balance_zero":None},
                       {"auto_reload_enabled":True},{"auto_reload_enabled":None},{"account_id":"other"},
                       {"verified":False},{"ordinary_usage_allowed":None},{"active_work":True},
                       {"observed_at":NOW-301},{"observed_at":NOW+1}):
            with self.subTest(change=change):
                self.assertEqual(self.decision(replace(self.status,**change)).action,"hold")

    def test_missing_ambiguous_or_unspecified_target_holds(self):
        for profile in (replace(self.profile,trigger_window_minutes=None),replace(self.profile,trigger_window_minutes=1)):
            self.assertEqual(self.decision(profile=profile).action,"hold")
        status=replace(self.status,windows=(self.status.windows[0],replace(self.status.windows[0],key="other")))
        self.assertEqual(self.decision(status).action,"hold")

    def test_legacy_single_snapshot_never_establishes_anchor(self):
        old={"windows":[{"key":"short","resets_at":NOW-120}]}
        self.assertEqual(decide(self.profile,self.status,old,[],{},NOW).action,"hold")

    def test_two_distinct_fresh_reads_required_for_anchor(self):
        state={}
        observe_fixed_resets(self.profile,self.status,state,NOW)
        observe_fixed_resets(self.profile,self.status,state,NOW+60)
        self.assertEqual(state["fixed_resets"],{})
        observe_fixed_resets(self.profile,replace(self.status,observed_at=NOW+59),state,NOW+59)
        self.assertEqual(state["fixed_resets"],{})
        observe_fixed_resets(self.profile,replace(self.status,observed_at=NOW+60),state,NOW+60)
        self.assertEqual(state["fixed_resets"]["short"]["resets_at"],NOW+18000)
        self.assertEqual(self.decision(state=state).action,"hold")

    def test_cli_honoring_next_check_establishes_anchor_before_expiration(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);config=folder/"config.json";snapshot=folder/"snapshot.json"
            config.write_text(json.dumps({"profiles":[asdict(self.profile)]}))
            def tick(status, now):
                row={**asdict(status),"auth_kind":"chatgpt"}
                snapshot.write_text(json.dumps({"accounts":{"plus":row}}))
                args=["--config",str(config),"--status",str(snapshot),"--state-dir",str(folder/"runtime"),
                      "--now",iso(now)]
                output=io.StringIO()
                with contextlib.redirect_stdout(output): self.assertEqual(main(args),0)
                return json.loads(output.getvalue())["decisions"][0]
            first=tick(self.status,NOW)
            second_at=timestamp(first["next_check_at"])
            self.assertEqual(second_at,NOW+60)
            second=tick(replace(self.status,observed_at=second_at),second_at)
            expiration_at=timestamp(second["next_check_at"])
            self.assertEqual(expiration_at,NOW+18060)
            fresh=replace(self.status,observed_at=expiration_at,
                          windows=(replace(self.status.windows[0],resets_at=expiration_at+18000),self.status.windows[1]))
            third=tick(fresh,expiration_at)
            self.assertEqual(third["action"],"would_request")
            self.assertEqual(third["trigger_at"],NOW+18000)

    def test_stale_and_wrong_identity_reads_do_not_form_anchor(self):
        state={}
        observe_fixed_resets(self.profile,self.status,state,NOW)
        for status,now in ((replace(self.status,account_id="other",observed_at=NOW+60),NOW+60),
                           (replace(self.status,observed_at=NOW+60),NOW+400)):
            observe_fixed_resets(self.profile,status,state,now)
        self.assertEqual(state["fixed_resets"],{})

    def test_drifting_idle_clock_never_mints_new_opportunities(self):
        state=copy.deepcopy(self.state)
        keys=[]
        for shift in (0,60,3600,18000,36000):
            status=replace(self.status,observed_at=NOW+shift,
                           windows=(replace(self.status.windows[0],resets_at=NOW+shift+18000),self.status.windows[1]))
            observe_fixed_resets(self.profile,status,state,NOW+shift)
            keys.append(self.decision(status,state,now=NOW+shift).opportunity_id)
        self.assertEqual(len(set(keys)),1)
        self.assertIsNotNone(keys[0])
        self.assertEqual(state["fixed_resets"]["short"]["resets_at"],NOW-120)

    def test_next_check_uses_fixed_anchor_instead_of_drifting_api_estimate(self):
        state=copy.deepcopy(self.state)
        state["fixed_resets"]["short"]["resets_at"]=NOW+3600
        decision=self.decision(state=state)
        self.assertEqual(decision.action,"hold")
        self.assertEqual(decision.next_check_at,NOW+3660)

    def test_expired_non_target_bucket_invalidates_completion(self):
        result=self.evidence()
        reads=tuple(replace(s,windows=(s.windows[0],replace(s.windows[1],resets_at=NOW-120)))
                    for s in result.status_reads)
        self.assertIsNone(verify_completed_request(self.decision(),self.profile,
                                                   replace(result,status_reads=reads),NOW,NOW+62))

    def test_fixed_anchor_must_expire_with_margin(self):
        for reset in (NOW+100,NOW-59):
            state=copy.deepcopy(self.state);state["fixed_resets"]["short"]["resets_at"]=reset
            self.assertEqual(self.decision(state=state).action,"hold")

    def test_success_requires_exact_completed_ok_and_matching_context(self):
        valid=self.evidence();decision=self.decision()
        self.assertIsNotNone(verify_completed_request(decision,self.profile,valid,NOW,NOW+62))
        for change in ({"completed":False},{"response_text":"OK."},{"disposable":False},
                       {"account_id":"other"},{"model_id":"other"},{"thread_id":None},
                       {"requested_at":NOW-1},{"completed_at":NOW+63},{"status_reads":()}):
            with self.subTest(change=change):
                self.assertIsNone(verify_completed_request(decision,self.profile,replace(valid,**change),NOW,NOW+62))

    def test_post_reads_need_distinct_fixed_future_reset_near_request_plus_duration(self):
        valid=self.evidence();first,second=valid.status_reads
        for reads in ((first,first),(second,first),
                      (first,replace(second,windows=(replace(second.windows[0],resets_at=NOW+18001),second.windows[1]))),
                      tuple(replace(s,windows=(replace(s.windows[0],resets_at=NOW+19000),s.windows[1])) for s in (first,second)),
                      (first,replace(second,account_id="other")),
                      (first,replace(second,auto_reload_enabled=None))):
            with self.subTest(reads=reads):
                self.assertIsNone(verify_completed_request(self.decision(),self.profile,replace(valid,status_reads=reads),NOW,NOW+62))
        self.assertIsNone(verify_completed_request(self.decision(),self.profile,valid,NOW,NOW+400))

    def test_success_updates_anchor_and_tiny_request_still_zero_never_duplicates(self):
        self.assertEqual(self.send(),"success")
        self.assertEqual(self.state["fixed_resets"]["short"]["resets_at"],NOW+18000)
        for shift in (62,300,3600):
            status=replace(self.status,observed_at=NOW+shift)
            self.assertEqual(self.decision(status,now=NOW+shift).action,"hold")
        self.assertNotIn("response_text",json.dumps(self.state))
        self.assertEqual(self.state["completed_disposable"]["cleanup"],"pending")

    def test_bare_success_or_unproven_retry_is_uncertain(self):
        for result in (RequestResult("success"),RequestResult("safe_retry"),RequestResult("unexpected")):
            state=copy.deepcopy(self.state)
            self.assertEqual(self.send(result,state),"uncertain")
            self.assertEqual(self.decision(state=state).action,"hold")

    def test_save_failure_before_send_cannot_dispatch(self):
        calls=[]
        class Fake:
            enabled=True
            def request(*args): calls.append(args)
        def fail(): raise OSError("synthetic storage failure")
        with self.assertRaises(OSError):
            dispatch(self.decision(),self.profile,Fake(),self.state,NOW,fail,False)
        self.assertEqual(calls,[])
        self.assertIn("inflight",self.state)

    def test_crash_before_response_persists_marker_and_restart_holds(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Store(folder);state=store.load();state["accounts"]["plus"]=copy.deepcopy(self.state)
            account=state["accounts"]["plus"]
            class Fake:
                enabled=True
                def request(*args):
                    self_test.assertIn("inflight",store.load()["accounts"]["plus"])
                    raise KeyboardInterrupt()
            self_test=self
            with store.locked():
                with self.assertRaises(KeyboardInterrupt):
                    dispatch(self.decision(),self.profile,Fake(),account,NOW,lambda:store.save(state),False,clock=lambda:NOW)
            self.assertEqual(self.decision(state=store.load()["accounts"]["plus"]).action,"hold")

    def test_success_and_dedup_survive_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Store(folder);state=store.load();state["accounts"]["plus"]=copy.deepcopy(self.state)
            with store.locked():
                self.assertEqual(self.send(state=state["accounts"]["plus"],save=lambda:store.save(state)),"success")
            account=store.load()["accounts"]["plus"]
            self.assertEqual(self.decision(state=account).action,"hold")
            self.assertEqual(len(account["handled_windows"]),1)

    def test_slow_save_expires_decision_before_send(self):
        calls=[];saves=[]
        class Fake:
            enabled=True
            def request(*args): calls.append(args)
        self.assertEqual(dispatch(self.decision(),self.profile,Fake(),self.state,NOW,
                                  lambda:saves.append(copy.deepcopy(self.state)),False,
                                  clock=lambda:NOW+301),"hold")
        self.assertEqual(calls,[])
        self.assertIn("inflight",saves[0])
        self.assertNotIn("inflight",saves[-1])

    def test_empty_or_missing_trigger_coverage_holds(self):
        for durations in ((),(10080,),(300,)):
            self.assertEqual(self.decision(profile=replace(self.profile,assumed_windows_minutes=durations)).action,"hold")

    def test_stale_or_mismatched_decision_never_dispatches(self):
        calls=[]
        class Fake:
            enabled=True
            def request(*args): calls.append(args)
        for decision,now in ((self.decision(),NOW+301),(replace(self.decision(),account_id="other"),NOW),
                             (replace(self.decision(),opportunity_id="invented"),NOW)):
            self.assertEqual(dispatch(decision,self.profile,Fake(),copy.deepcopy(self.state),now,lambda:None,False),"hold")
        self.assertEqual(calls,[])

    def test_next_window_uses_verified_anchor_not_latest_drifting_read(self):
        self.assertEqual(self.send(),"success")
        self.state["completed_disposable"]["cleanup"]="archived"
        later=NOW+18060
        status=replace(self.status,observed_at=later,windows=(replace(self.status.windows[0],resets_at=later+18000),self.status.windows[1]))
        observe_fixed_resets(self.profile,status,self.state,later)
        decision=self.decision(status,now=later)
        self.assertEqual(decision.action,"would_request")
        self.assertEqual(decision.trigger_at,NOW+18000)
        self.assertNotEqual(decision.opportunity_id,self.state["attempt"]["id"])


class Cleanup(Fixture, unittest.TestCase):
    def adapter(self, first=None, second=None, failure=False):
        good=ThreadStatus("fixture-disposable","plus",True,False,True)
        calls=[]
        class Fake:
            enabled=True
            def read_thread(*args):
                calls.append(("read",args[-2:]))
                return (first or good) if len(calls)==1 else (second or replace(good,archived=True))
            def archive(*args):
                calls.append(("archive",args[-2:]))
                if failure: raise TimeoutError()
        return Fake(),calls

    def prepare(self):
        self.assertEqual(self.send(),"success")

    def test_cleanup_disabled_by_default(self):
        self.prepare();adapter,calls=self.adapter()
        self.assertEqual(archive_completed_disposable(self.profile,adapter,self.state,lambda:None),"dry_run")
        self.assertEqual(archive_completed_disposable(self.profile,DisabledArchiveAdapter(),self.state,lambda:None,False),"disabled")
        self.assertEqual(calls,[])

    def test_archive_exact_completed_disposable_and_verify(self):
        self.prepare();adapter,calls=self.adapter();saves=[]
        self.assertEqual(archive_completed_disposable(self.profile,adapter,self.state,lambda:saves.append(copy.deepcopy(self.state)),False),"archived")
        self.assertEqual([c[0] for c in calls],["read","archive","read"])
        self.assertTrue(all(c[1]==("plus","fixture-disposable") for c in calls))
        self.assertEqual(saves[0]["completed_disposable"]["cleanup"],"inflight")
        self.assertEqual(archive_completed_disposable(self.profile,adapter,self.state,lambda:None,False),"archived")
        self.assertEqual(len(calls),3)

    def test_cleanup_never_touches_wrong_chat_account_or_incomplete_work(self):
        for first in (ThreadStatus("other","plus",True,False,True),ThreadStatus("fixture-disposable","other",True,False,True),
                      ThreadStatus("fixture-disposable","plus",False,False,True),ThreadStatus("fixture-disposable","plus",True,False,False)):
            self.setUp();self.prepare();adapter,calls=self.adapter(first=first)
            self.assertEqual(archive_completed_disposable(self.profile,adapter,self.state,lambda:None,False),"hold")
            self.assertEqual([c[0] for c in calls],["read"])

    def test_archive_timeout_not_retried_and_read_can_reconcile(self):
        self.prepare();adapter,calls=self.adapter(failure=True)
        self.assertEqual(archive_completed_disposable(self.profile,adapter,self.state,lambda:None,False),"uncertain")
        adapter,calls=self.adapter()
        self.assertEqual(archive_completed_disposable(self.profile,adapter,self.state,lambda:None,False),"uncertain")
        self.assertEqual([c[0] for c in calls],["read"])
        adapter,calls=self.adapter(first=ThreadStatus("fixture-disposable","plus",True,True,True))
        self.assertEqual(archive_completed_disposable(self.profile,adapter,self.state,lambda:None,False),"archived")
        self.assertEqual([c[0] for c in calls],["read"])


class Config(unittest.TestCase):
    def test_heuristic_requires_explicit_target_and_boolean_flags(self):
        base=json.loads((ROOT/"examples/config.single-account.json").read_text())
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"config.json"
            for change in ({"activity_policy":"typo"},{"activity_policy":"remaining_percent_heuristic","trigger_window_minutes":None},
                           {"trigger_window_minutes":True},{"trigger_window_minutes":0}):
                payload=copy.deepcopy(base);payload["profiles"][0].update(change);path.write_text(json.dumps(payload))
                with self.assertRaises(ValueError): load_config(path)

    def test_changed_identity_binding_cannot_reuse_state(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);config=folder/"config.json";runtime=folder/"runtime"
            payload=json.loads((ROOT/"examples/config.single-account.json").read_text())
            payload["profiles"][0]["expected_account_id_hash"]="a"*16
            config.write_text(json.dumps(payload))
            args=["--config",str(config),"--state-dir",str(runtime),"--now","2026-10-14T12:02:00Z"]
            with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(main(args),0)
            before=(runtime/"state.json").read_bytes()
            payload["profiles"][0]["expected_account_id_hash"]="b"*16;config.write_text(json.dumps(payload))
            with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(main(args),2)
            self.assertEqual((runtime/"state.json").read_bytes(),before)


if __name__ == "__main__": unittest.main()
