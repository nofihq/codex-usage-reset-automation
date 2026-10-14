from helpers import private_temp
import contextlib
from dataclasses import asdict, replace
import io
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError

from optimizer.adapters import (SnapshotStatusAdapter, TrackerAdapter, ingest_events,
                                parse_timeline, read_json, retry_after)
from optimizer.core import (Event, Policy, Profile, Status, Window, decide, timestamp)
from optimizer.request import DisabledRequestAdapter, RequestResult, dispatch
from optimizer.storage import LOG_BYTES, LOG_FILES, Store, increment
from optimizer.__main__ import main
from optimizer.probe import ALLOWED, identity_hash, sanitized_limits

NOW = timestamp("2026-10-14T12:02:00Z")
ROOT = Path(__file__).resolve().parents[1]


class Decisions(unittest.TestCase):
    def setUp(self):
        self.profile = Profile("plus", "Plus", (300,10080), True, "fixture-model", True, True, True, True, True)
        self.status = Status("plus", NOW, (Window("p",0,NOW+18000,300), Window("w",0,NOW+604800,10080)),
                             ("fixture-model",), True, True, True, False, False, True)
        self.previous = {"windows":[{"key":"p","resets_at":NOW-120}]}

    def decision(self, **kwargs):
        return decide(kwargs.get("profile", self.profile), kwargs.get("status", self.status),
                      kwargs.get("previous", self.previous), kwargs.get("events", []),
                      kwargs.get("state", {}), kwargs.get("now", NOW))

    def test_verified_expiration_candidate(self):
        self.assertEqual(self.decision().action, "would_request")

    def test_missing_status_holds(self):
        self.assertEqual(self.decision(status=None).reason, "Account status unavailable")

    def test_permission_null_or_false_holds_even_at_zero_percent(self):
        for permission in (None,False):
            self.assertEqual(self.decision(status=replace(self.status, ordinary_usage_allowed=permission)).action,"hold")

    def test_identity_and_provenance_holds(self):
        for status in (replace(self.status, account_id="other"), replace(self.status,verified=False)):
            self.assertEqual(self.decision(status=status).action,"hold")

    def test_stale_future_missing_duplicate_invalid_buckets(self):
        statuses = [replace(self.status,observed_at=NOW-301),replace(self.status,observed_at=NOW+1),
                    replace(self.status,windows=()),replace(self.status,windows=(self.status.windows[0],)*2),
                    replace(self.status,windows=(Window("p",-1,NOW+200,300),)),
                    replace(self.status,windows=(Window("p",0,NOW+200,0),))]
        for status in statuses:
            with self.subTest(status=status):
                self.assertEqual(self.decision(status=status).action,"hold")

    def test_elapsed_time_only_requests_fresh_status(self):
        status=replace(self.status,windows=(Window("p",100,NOW-10,300),))
        self.assertEqual(self.decision(status=status).action,"check_status")

    def test_exhausted_weekly_blocks_even_after_short_reset(self):
        status=replace(self.status,windows=(self.status.windows[0],replace(self.status.windows[1],used_percent=100)))
        self.assertEqual(self.decision(status=status).action,"hold")

    def test_existing_activity_blocks_disposable_request(self):
        self.assertEqual(self.decision(status=replace(self.status,windows=(replace(self.status.windows[0],used_percent=0.1),))).action,"hold")

    def test_unverified_gates_and_model_holds(self):
        for flag in ("assumptions_verified","subscription_auth_verified","model_verified","usage_impact_verified","reset_behavior_verified","paid_fallback_prevented_verified"):
            self.assertEqual(self.decision(profile=replace(self.profile,**{flag:False})).action,"hold")
        self.assertEqual(self.decision(status=replace(self.status,model_ids=())).action,"hold")

    def test_public_reset_not_personal_refill(self):
        for confirmed in (True,False,None):
            event=Event("event","global_reset",NOW-120,"https://codex-reset.com/",confirmed,"announced")
            self.assertEqual(self.decision(previous=None,events=[event]).action,"hold")
            old=replace(self.status,observed_at=NOW-150)
            self.assertEqual(self.decision(status=old,previous=None,events=[event]).action,"check_status")

    def test_banked_notice_never_candidate(self):
        event=Event("grant","banked_notice",NOW-120,"https://codex-reset.com/",True,"announced")
        self.assertEqual(self.decision(previous=None,events=[event]).action,"hold")

    def test_assumed_durations_do_not_control_timer(self):
        d=self.decision(profile=replace(self.profile,assumed_windows_minutes=(1,)))
        self.assertEqual(d.next_check_at,NOW+18060)

    def test_idempotency_and_uncertain_holds(self):
        for state in ({"handled_through":NOW-120},{"inflight":"key"},{"uncertain":True}):
            self.assertEqual(self.decision(state=state).action,"hold")

    def test_retry_time_and_count(self):
        d=self.decision()
        attempt={"id":d.opportunity_id,"count":1,"outcome":"safe_retry","retry_at":NOW+60}
        self.assertEqual(self.decision(state={"attempt":attempt}).action,"hold")
        attempt["retry_at"]=NOW
        self.assertEqual(self.decision(state={"attempt":attempt}).action,"would_request")
        attempt["count"]=2
        self.assertEqual(self.decision(state={"attempt":attempt}).action,"hold")


class Feed(unittest.TestCase):
    def events(self):
        return parse_timeline(read_json(ROOT/"fixtures/timeline.json",131072),NOW)

    def test_announced_unconfirmed_preserved(self):
        event=next(e for e in self.events() if e.event_id=="fixture-announced-unconfirmed")
        self.assertIs(event.confirmed,False)
        self.assertEqual(event.kind,"global_reset")

    def test_first_run_baseline_and_duplicate_suppression(self):
        state={}
        self.assertEqual(ingest_events(self.events(),state,NOW),[])
        self.assertEqual(ingest_events(self.events(),state,NOW+60),[])
        self.assertNotIn("Ignore previous",json.dumps(state))
        self.assertFalse(state["feed"]["records"][next(k for k,v in state["feed"]["records"].items() if v["event_id"]=="fixture-announced-unconfirmed")]["confirmed"])

    def test_related_banked_notices_are_not_two_credits(self):
        state={"feed":{"initialized":True}}
        banked=[e for e in self.events() if e.kind=="banked_notice"]
        self.assertEqual(len(ingest_events(banked,state,NOW)),1)
        self.assertNotIn("balance",json.dumps(state))

    def test_future_malformed_and_old_events_ignored(self):
        payload={"events":[{"id":"x","announced_at":"2027-10-14T12:00:00Z","group":"reset","announcement_state":"announced"},
                           {"id":"x","announced_at":"2025-10-14T12:00:00Z","group":"reset","announcement_state":"announced"},
                           {"id":"x","announced_at":"bad","group":"reset","announcement_state":"announced"}]}
        self.assertEqual(parse_timeline(payload,NOW),[])
        with self.assertRaises(ValueError): parse_timeline({"weird":[]},NOW)

    def test_ledger_retention_and_watermark(self):
        state={"feed":{"initialized":True,"seen":{str(i):NOW-40*86400 for i in range(300)}}}
        ingest_events(self.events(),state,NOW)
        self.assertLessEqual(len(state["feed"]["seen"]),256)
        self.assertEqual(ingest_events(self.events(),state,NOW+40*86400),[])

    def test_retry_after_seconds_date_and_invalid(self):
        self.assertEqual(retry_after("3600",NOW),NOW+3600)
        self.assertEqual(retry_after("Wed, 14 Oct 2026 13:02:00 GMT",NOW),NOW+3600)
        self.assertEqual(retry_after(None,NOW),NOW+3600)

    def test_429_honors_retry_after_without_immediate_retry(self):
        calls=[]
        def opener(req,timeout):
            calls.append(req)
            raise HTTPError(req.full_url,429,"limit",{"Retry-After":"20000"},None)
        state={}; adapter=TrackerAdapter("optimizer-test/0.1 (+https://example.invalid)",opener=opener)
        self.assertEqual(adapter.read(state,NOW)[1],"rate_limited")
        self.assertEqual(adapter.read(state,NOW+60)[1],"not_due")
        self.assertEqual(state["feed"]["fetch_after"],NOW+20000)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0].method,"GET")

    def response(self,headers=None,content=b'{"events":[]}'):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def geturl(self): return "https://codex-reset.com/api/timeline"
            def read(self,limit): return content[:limit]
        r=Response(); r.headers=headers or {}; return r

    def test_freshness_cache_and_conditional_headers(self):
        calls=[]
        def opener(req,timeout):
            calls.append(req)
            return self.response({"x-published-checked-at":"2026-10-14T12:01:00Z","x-published-expires-at":"2026-10-14T12:03:00Z","Cache-Control":"max-age=20000","ETag":"fixture"})
        state={}; adapter=TrackerAdapter("test/1",opener=opener)
        self.assertEqual(adapter.read(state,NOW)[1],"ok")
        self.assertEqual(state["feed"]["fetch_after"],NOW+20000)
        adapter.read(state,NOW+20000)
        self.assertEqual(calls[-1].get_header("If-none-match"),"fixture")

    def test_unknown_or_expired_freshness_holds(self):
        for headers in ({},{"x-published-checked-at":"2026-10-14T11:00:00Z","x-published-expires-at":"2026-10-14T11:01:00Z"}):
            adapter=TrackerAdapter("test/1",opener=lambda *a,**k:self.response(headers))
            self.assertIn(adapter.read({},NOW)[1],{"unavailable","stale"})

    def test_oversized_response_and_redirect_hold(self):
        oversized=TrackerAdapter("test/1",opener=lambda *a,**k:self.response(content=b"x"*1048577))
        self.assertEqual(oversized.read({},NOW)[1],"too_large")
        response=self.response(); response.geturl=lambda:"https://example.invalid/"
        redirected=TrackerAdapter("test/1",opener=lambda *a,**k:response)
        self.assertEqual(redirected.read({},NOW)[1],"unexpected_redirect")

    def test_304_no_historical_replay(self):
        def opener(req,timeout): raise HTTPError(req.full_url,304,"cached",{},None)
        self.assertEqual(TrackerAdapter("test/1",opener=opener).read({},NOW),([],"not_modified"))


class Requests(unittest.TestCase):
    setUp = Decisions.setUp
    decision = Decisions.decision
    def test_disabled_and_dry_run_do_not_call_adapter(self):
        self.assertEqual(dispatch(self.decision(),self.profile,DisabledRequestAdapter(),{},NOW,lambda:None),"dry_run")
        self.assertEqual(dispatch(self.decision(),self.profile,DisabledRequestAdapter(),{},NOW,lambda:None,dry_run=False),"disabled")

    def test_one_bounded_retry_then_hold(self):
        calls=[]; saves=[]; state={}
        class Fake:
            enabled=True
            def request(self,*args):
                self_test.assertIn("inflight",state)
                calls.append(args)
                return RequestResult("safe_retry")
        self_test=self
        d=self.decision()
        save=lambda:saves.append(json.loads(json.dumps(state)))
        self.assertEqual(dispatch(d,self.profile,Fake(),state,NOW,save,False),"safe_retry")
        self.assertEqual(dispatch(d,self.profile,Fake(),state,NOW+30,save,False),"hold")
        self.assertEqual(dispatch(d,self.profile,Fake(),state,NOW+60,save,False),"hold")
        self.assertEqual(dispatch(d,self.profile,Fake(),state,NOW+120,save,False),"duplicate")
        self.assertEqual(len(calls),2)
        self.assertEqual(len(saves),4)

    def test_uncertain_never_retried(self):
        class Fake:
            enabled=True
            def request(self,*a): raise TimeoutError()
        state={}; d=self.decision()
        self.assertEqual(dispatch(d,self.profile,Fake(),state,NOW,lambda:None,False),"uncertain")
        self.assertEqual(dispatch(d,self.profile,Fake(),state,NOW+60,lambda:None,False),"uncertain")

    def test_success_duplicate_and_unverified_block(self):
        class Fake:
            enabled=True
            def request(self,*a): return RequestResult("success")
        state={}; d=self.decision()
        self.assertEqual(dispatch(d,replace(self.profile,usage_impact_verified=False),Fake(),state,NOW,lambda:None,False),"disabled")
        self.assertEqual(dispatch(d,self.profile,Fake(),state,NOW,lambda:None,False),"success")
        self.assertEqual(dispatch(d,self.profile,Fake(),state,NOW,lambda:None,False),"duplicate")


class StorageAndCLI(unittest.TestCase):
    def test_probe_allowlist_and_sanitization_preserves_unknown(self):
        self.assertNotIn("turn/start",ALLOWED)
        self.assertNotIn("account/login/start",ALLOWED)
        self.assertNotIn("account/rateLimitResetCredit/consume",ALLOWED)
        raw={"accountId":None,"ordinaryUsageAllowed":None,"email":"private@example.invalid",
             "accessToken":"secret-fixture","rateLimitsByLimitId":{"codex":{"primary":{"usedPercent":0,"windowDurationMins":10080,"resetsAt":NOW+1000},"credits":{"balance":"0"}}}}
        result=sanitized_limits(raw)
        self.assertIsNone(result["ordinary_usage_allowed"])
        self.assertIsNone(result["account_identity_hash"])
        self.assertNotIn("secret-fixture",json.dumps(result))
        self.assertNotIn("private@",json.dumps(result))
        self.assertEqual(len(identity_hash("fixture-id")),16)

    def test_snapshot_missing_identity_permission_invalid_auth_and_zero(self):
        with private_temp() as temp:
            path=Path(temp)/"snapshot.json"
            base=json.loads((ROOT/"fixtures/status-after.json").read_text())
            for field,value in (("auth_kind","api_key"),("account_id",None),("ordinary_usage_allowed","true")):
                payload=json.loads(json.dumps(base)); payload["accounts"]["plus"][field]=value
                path.write_text(json.dumps(payload)); status=SnapshotStatusAdapter(path).read("plus")
                self.assertTrue(status is None or status.account_id!="plus")
            payload=json.loads(json.dumps(base)); del payload["accounts"]["plus"]["windows"][0]["used_percent"]
            path.write_text(json.dumps(payload)); self.assertIsNone(SnapshotStatusAdapter(path).read("plus"))
            path.write_text(json.dumps(base)); self.assertEqual(SnapshotStatusAdapter(path).read("plus").windows[0].used_percent,0)

    def test_atomic_state_limits_corruption_and_lock(self):
        with private_temp() as temp:
            store=Store(temp); state=store.load(); store.save(state)
            self.assertEqual(store.load(),state)
            with store.locked():
                with self.assertRaises(ValueError):
                    with Store(temp).locked(): pass
            with self.assertRaises(ValueError): store.save({"huge":"x"*131073})
            self.assertEqual(store.load(),state)
            self.assertEqual(list(Path(temp).glob("*.tmp")),[])
            store.path.write_text("bad")
            with self.assertRaises(ValueError): store.load()

    def test_logs_rotate_and_retention(self):
        with private_temp() as temp:
            store=Store(temp)
            entry=json.dumps({"at":NOW,"code":"hold"})+"\n"
            for i in range(6):
                (Path(temp)/"events.log").write_text(entry*(LOG_BYTES//len(entry)))
                (Path(temp)/"events.log").chmod(0o600)
                store.log(NOW,"hold")
            paths=list(Path(temp).glob("events.log*"))
            self.assertLessEqual(len(paths),LOG_FILES)
            self.assertTrue(all(p.stat().st_size<=LOG_BYTES for p in paths))
            store.log(NOW+8*86400,"hold")
            self.assertEqual(len(list(Path(temp).glob("events.log*"))),1)
            self.assertEqual(len((Path(temp)/"events.log").read_text().splitlines()),1)

    def test_metrics_bounded_fixed_labels(self):
        state={"metrics":{"ticks":10**9}}; increment(state,"ticks")
        self.assertEqual(state["metrics"]["ticks"],10**9)
        with self.assertRaises(ValueError): increment(state,"feed text")

    def run_cli(self,args):
        out=io.StringIO()
        with contextlib.redirect_stdout(out): code=main(args)
        return code,json.loads(out.getvalue())

    def test_cli_two_accounts_missing_status_and_replay(self):
        with private_temp() as temp:
            base=["--config",str(ROOT/"examples/config.fixture.json"),"--state-dir",temp]
            code,out=self.run_cli(base+["--now","2026-10-14T10:00:00Z"])
            self.assertEqual(code,0); self.assertEqual(len(out["decisions"]),2)
            self.assertTrue(all(d["action"]=="hold" for d in out["decisions"]))
            for fixture,now in (("status-before.json","2026-10-14T10:00:00Z"),("status-after.json","2026-10-14T12:02:00Z")):
                code,out=self.run_cli(base+["--status",str(ROOT/"fixtures"/fixture),"--now",now,"--feed-fixture",str(ROOT/"fixtures/timeline.json")])
                self.assertEqual(code,0); self.assertFalse(out["live_requests_enabled"])
            self.assertEqual(out["new_feed_hints"],1)
            code,out=self.run_cli(base+["--status",str(ROOT/"fixtures/status-after.json"),"--now","2026-10-14T12:02:00Z","--feed-fixture",str(ROOT/"fixtures/timeline.json")])
            self.assertEqual(out["new_feed_hints"],0)
            self.assertEqual(out["decisions"][0]["action"],"hold")
            code,out=self.run_cli(base+["--now","2026-10-14T09:00:00Z"])
            self.assertEqual(code,2); self.assertEqual(out["action"],"hold")

    def test_oversized_nonfinite_and_naive_inputs(self):
        with private_temp() as temp:
            path=Path(temp)/"input"; path.write_text("x"*100)
            with self.assertRaises(ValueError): read_json(path,10)
            path.write_text('{"used":NaN}')
            with self.assertRaises(ValueError): read_json(path,100)
        with self.assertRaises(ValueError): timestamp("2026-10-14T12:00:00")


if __name__=="__main__": unittest.main()
