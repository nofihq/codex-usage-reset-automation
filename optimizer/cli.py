"""Composable commands; JSON output and no live inference command."""
import argparse
import json
from pathlib import Path
import sys


def emit(value):
    print(json.dumps(value, indent=2, allow_nan=False))


def state_default():
    return str(Path.home()/".local"/"state"/"codex-usage-reset-automation")


def doctor(config_path=None):
    """Offline readiness only; no account reads, network, or state writes."""
    result = {"mode": "offline", "python": ".".join(map(str, sys.version_info[:3])),
              "platform_supported": sys.platform.startswith("linux") and sys.version_info >= (3, 10),
              "config_valid": None, "profile_count": 0, "live_requests_enabled": False,
              "account_reads": 0, "auth": "not inspected", "dependencies": "Python standard library only"}
    if config_path:
        try:
            from .__main__ import load_config
            _, profiles, _ = load_config(config_path)
            result.update(config_valid=True, profile_count=len(profiles))
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            result["config_valid"] = False
    result["ok"] = result["platform_supported"] and result["config_valid"] is not False
    result["next_step"] = "Run check with local configuration, or explicitly opt into probe for an isolated home"
    return result


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    # Preserve the original finite tick flag interface.
    if args and args[0].startswith("--") and args[0] not in {"--help", "--json"}:
        from .__main__ import main as tick
        return tick(args)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="All commands already emit JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    doc = sub.add_parser("doctor", help="Offline environment/config check; never reads account authentication")
    doc.add_argument("--config")
    chk = sub.add_parser("check", help="Validate configuration without reading accounts or writing state")
    chk.add_argument("--config", required=True)
    dry = sub.add_parser("dry-run", help="One finite planning tick; model dispatch always disabled")
    dry.add_argument("--config", default="config.json")
    dry.add_argument("--status")
    dry.add_argument("--due-only", action="store_true", help="Skip read-only account probes until their saved deadlines")
    dry.add_argument("--read-accounts", action="store_true", help="Opt-in read-only metadata from isolated Codex homes")
    dry.add_argument("--feed-fixture")
    dry.add_argument("--fetch-feed", action="store_true")
    dry.add_argument("--user-agent")
    dry.add_argument("--state-dir", default=state_default())
    dry.add_argument("--now")
    prob = sub.add_parser("probe", help="Opt-in official account metadata; requires a separate signed-in home")
    prob.add_argument("--config", required=True)
    prob.add_argument("--alias", required=True)
    prob.add_argument("--check-version-only", action="store_true", help="Discover Codex version using an empty temporary home")
    parsed = parser.parse_args(args)
    if parsed.command == "doctor":
        result = doctor(parsed.config); emit(result)
        return 0 if result["ok"] else 2
    if not sys.platform.startswith("linux") or sys.version_info < (3, 10):
        emit({"ok": False, "action": "hold", "reason": "Supported runtime is Linux with Python 3.10+; Windows requires WSL2"})
        return 2
    if parsed.command == "check":
        result = doctor(parsed.config); emit(result)
        return 0 if result["ok"] else 2
    if parsed.command == "dry-run":
        from .__main__ import main as tick
        flags = ["--config", parsed.config, "--state-dir", parsed.state_dir]
        for name in ("status", "feed_fixture", "user_agent", "now"):
            value = getattr(parsed, name)
            if value is not None:
                flags += ["--"+name.replace("_", "-"), value]
        for name in ("read_accounts", "fetch_feed", "due_only"):
            if getattr(parsed, name): flags.append("--"+name.replace("_", "-"))
        return tick(flags)
    from .__main__ import load_config
    from .probe import REVIEWED_VERSIONS, installed_version, probe, status_from_report
    try:
        config, profiles, _ = load_config(parsed.config)
        row = next(row for row in config["profiles"] if row["account_id"] == parsed.alias)
        if parsed.check_version_only:
            version = installed_version()
            emit({"mode": "offline", "codex_version": version, "reviewed": version in REVIEWED_VERSIONS,
                  "account_reads": 0})
            return 0 if version in REVIEWED_VERSIONS else 2
        report = probe(row.get("codex_home"))
        status = status_from_report(parsed.alias, row.get("expected_account_id_hash"), report)
        # Readiness does not claim auth solely because percentages are present.
        report.update(alias=parsed.alias, status_available=status is not None,
                      expected_identity_matches=status is not None)
        emit(report)
        return 0 if report.get("limits_read") == "completed" and report.get("models_read") == "completed" else 2
    except (OSError, ValueError, KeyError, TypeError, AttributeError, StopIteration):
        emit({"mode": "read_only", "action": "hold", "reason": "Invalid configuration or unknown alias"})
        return 2
