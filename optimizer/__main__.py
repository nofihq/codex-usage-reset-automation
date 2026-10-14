"""One finite dry-run tick. No scheduler, login, redemption or model invocation."""
import argparse
from dataclasses import asdict
import json
import re
import time
from pathlib import Path

from .adapters import FEED_BYTES, SnapshotStatusAdapter, TrackerAdapter, ingest_events, parse_timeline, read_json
from .core import Policy, Profile, decide, iso, timestamp
from .storage import Store, increment
from .platforms import state_default


def load_config(path):
    config = read_json(path, 16384)
    rows = config["profiles"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 16:
        raise ValueError("One to sixteen profiles required")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("Profiles must be objects")
    profiles = [Profile(**{**{k:v for k,v in row.items() if k not in {"codex_home", "expected_account_id_hash"}},
                           "assumed_windows_minutes": tuple(row["assumed_windows_minutes"])}) for row in rows]
    base = Path(path).expanduser().resolve().parent
    homes = []
    for row in rows:
        expected = row.get("expected_account_id_hash")
        if expected is not None and (not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{16}", expected)):
            raise ValueError("Expected identity must be a 16-character hash")
        home = row.get("codex_home")
        if home is not None:
            if not isinstance(home,str) or not home:
                raise ValueError("Invalid isolated account home")
            resolved = Path(home).expanduser()
            if not resolved.is_absolute(): resolved = base / resolved
            row["codex_home"] = str(resolved.resolve())
            if resolved.resolve() == Path.home()/".codex":
                raise ValueError("Use a separate account home, not the default Codex home")
            homes.append(row["codex_home"])
    if len(set(homes)) != len(homes):
        raise ValueError("Account homes must be distinct")
    if len({p.account_id for p in profiles}) != len(profiles):
        raise ValueError("Profiles need distinct local aliases")
    for p in profiles:
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", p.account_id):
            raise ValueError("Invalid expected account identity")
        if len(p.assumed_windows_minutes) > 16:
            raise ValueError("Too many window assumptions")
        if any(type(v) is not int or v <= 0 for v in p.assumed_windows_minutes):
            raise ValueError("Invalid window assumptions")
        for flag in (p.assumptions_verified, p.subscription_auth_verified, p.model_verified,
                     p.usage_impact_verified, p.reset_behavior_verified, p.paid_fallback_prevented_verified):
            if type(flag) is not bool:
                raise ValueError("Verification flags must be booleans")
    policy = Policy(**config.get("policy", {}))
    if any(type(v) is not int or not 60 <= v <= 30*86400 for v in asdict(policy).values()):
        raise ValueError("Policy times must be bounded integers, at least 60 seconds")
    return config, profiles, policy


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--read-accounts", action="store_true", help="Opt-in official read-only status for configured isolated homes")
    parser.add_argument("--status", help="Explicit normalized JSON snapshot; omission holds")
    parser.add_argument("--feed-fixture", help="Explicit tracker JSON fixture")
    parser.add_argument("--fetch-feed", action="store_true", help="Opt-in keyless read-only public GET; no account calls")
    parser.add_argument("--user-agent", help="Project name and contact URL for public feed")
    parser.add_argument("--state-dir", default=state_default())
    parser.add_argument("--now", help="ISO timestamp with timezone, for deterministic replay")
    args = parser.parse_args(argv)
    try:
        if args.read_accounts and args.now:
            raise ValueError("Live metadata reads cannot use a simulated clock")
        if args.read_accounts and args.status:
            raise ValueError("Choose snapshots or read-only accounts")
        config, profiles, policy = load_config(args.config)
        now = timestamp(args.now) if args.now else time.time()
        store = Store(args.state_dir)
        with store.locked():
            state = store.load()
            if now < state.get("last_tick_at", 0):
                raise ValueError("Clock moved backwards; inspect before continuing")
            # Never revive private state under unrelated/new account identities.
            if set(state["accounts"]) - {p.account_id for p in profiles}:
                raise ValueError("State account identities differ from config")
            events, feed_result = [], "disabled"
            if args.feed_fixture:
                events = parse_timeline(read_json(args.feed_fixture, FEED_BYTES), now)
                feed_result = "fixture"
            elif args.fetch_feed:
                feed_config = config.get("feed", {})
                if feed_config.get("endpoint") != "https://codex-reset.com/api/timeline":
                    raise ValueError("Only verified timeline endpoint is supported")
                events, feed_result = TrackerAdapter(args.user_agent, feed_config.get("min_interval_seconds", 14400)).read(state, now)
            new_events = ingest_events(events, state, now) if feed_result in {"ok", "fixture"} else []
            adapter = SnapshotStatusAdapter(args.status) if args.status else None
            reports = []
            probes = []
            for index, profile in enumerate(profiles):
                account = state["accounts"].setdefault(profile.account_id, {})
                status = adapter.read(profile.account_id) if adapter else None
                if args.read_accounts:
                    from .probe import OfficialStatusAdapter
                    row = config["profiles"][index]
                    official = OfficialStatusAdapter(row.get("codex_home"), row.get("expected_account_id_hash"))
                    status = official.read(profile.account_id)
                    probes.append({"alias": profile.account_id, "report": official.report})
                decision_now = time.time() if args.read_accounts else now
                decision = decide(profile, status, account.get("previous"), new_events, account, decision_now, policy)
                increment(state, decision.action)
                store.log(now, decision.action)
                if status and status.verified and status.account_id == profile.account_id and status.ordinary_usage_allowed is True:
                    # Snapshot tracking only; reset feed never changes these clocks.
                    if 0 <= decision_now - status.observed_at <= policy.status_max_age_seconds:
                        account["previous"] = asdict(status)
                row = asdict(decision)
                row["next_check_at"] = iso(decision.next_check_at)
                reports.append(row)
            increment(state, "ticks")
            if feed_result == "ok":
                increment(state, "feed_ok")
            elif feed_result in {"stale", "unavailable", "http_error", "rate_limited", "unexpected_redirect", "too_large"}:
                increment(state, "feed_failed")
            state["last_tick_at"] = now
            store.save(state)
            print(json.dumps({"mode": "dry_run", "live_requests_enabled": False, "feed": feed_result,
                              "feed_source": "https://codex-reset.com/", "new_feed_hints": len(new_events),
                              "feed_hints": [asdict(e) for e in new_events],
                              "decisions": reports, "probes": probes}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        # No raw exception printing: inputs could include private paths or feed text.
        print(json.dumps({"mode": "dry_run", "action": "hold", "reason": "Invalid configuration, locked/corrupt storage, or invalid input; inspect locally"}))
        return 2


if __name__ == "__main__":
    from .cli import main as cli_main
    raise SystemExit(cli_main())
