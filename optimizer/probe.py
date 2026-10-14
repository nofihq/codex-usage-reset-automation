"""Opt-in official AppServer metadata reads in a separate, user-selected home.

Only Codex accesses its credential store. Never invoke a turn, login, or redemption.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import subprocess
import tempfile
import time
from decimal import Decimal, InvalidOperation

from .core import Status, Window, iso, timestamp

ALLOWED = {"initialize", "account/read", "account/rateLimits/read", "model/list"}
REVIEWED_VERSIONS = {"0.158.0", "0.159.2"}
CREDENTIAL_ENV = ("OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN", "OPENAI_ACCESS_TOKEN",
                  "OPENAI_BASE_URL", "OPENAI_ORG_ID", "OPENAI_PROJECT_ID")


class ProbeError(Exception):
    def __init__(self, reason, code=None):
        self.reason, self.code = reason, code


def child_environment(home):
    env = os.environ.copy()
    for key in CREDENTIAL_ENV:
        env.pop(key, None)
    env["CODEX_HOME"] = str(home)
    return env


def installed_version():
    """Version discovery uses an empty temporary home, never the owner's login."""
    try:
        with tempfile.TemporaryDirectory(prefix="optimizer-version-") as home:
            result = subprocess.run(["codex", "--version"], env=child_environment(home), cwd=home,
                                    capture_output=True, timeout=10, text=True)
        match = re.fullmatch(r"codex-cli (\d+\.\d+\.\d+)\s*", result.stdout)
        return match.group(1) if result.returncode == 0 and match else None
    except (OSError, subprocess.SubprocessError):
        return None


class ReadOnlyClient:
    def __init__(self, codex_home):
        if os.name != "posix":
            raise ProbeError("AppServer probe requires POSIX; use Linux or WSL2")
        if installed_version() not in REVIEWED_VERSIONS:
            raise ProbeError("Codex version unavailable or outside reviewed versions")
        home = Path(codex_home).expanduser().absolute()
        # No inspection of files inside the selected credential store.
        if home == Path.home()/".codex" or not home.is_dir() or home.is_symlink():
            raise ProbeError("A separate existing account home is required")
        self.process = subprocess.Popen(
            ["codex", "-c", 'forced_login_method="chatgpt"', "app-server", "--listen", "stdio://"],
            env=child_environment(home), cwd=home, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, bufsize=0)
        self.buffer = b""
        self.counter = 0

    def send(self, payload):
        self.process.stdin.write((json.dumps(payload)+"\n").encode())
        self.process.stdin.flush()

    def call(self, method, params=None):
        if method not in ALLOWED:
            raise ProbeError("Method prohibited")
        self.counter += 1
        message = {"id": self.counter, "method": method}
        if params is not None:
            message["params"] = params
        self.send(message)
        deadline = time.monotonic()+20
        total = len(self.buffer)
        while time.monotonic() < deadline:
            if b"\n" not in self.buffer:
                ready, _, _ = select.select([self.process.stdout], [], [], max(0, deadline-time.monotonic()))
                if not ready:
                    break
                block = os.read(self.process.stdout.fileno(), 8192)
                if not block:
                    raise ProbeError("AppServer closed; check runtime support locally")
                total += len(block)
                if total > 262144:
                    raise ProbeError("AppServer response exceeds bound")
                self.buffer += block
                continue
            line, self.buffer = self.buffer.split(b"\n", 1)
            try:
                response = json.loads(line)
            except ValueError:
                raise ProbeError("AppServer returned unsupported framing")
            if not isinstance(response, dict):
                raise ProbeError("AppServer returned invalid framing")
            if "method" in response:
                if "id" in response:
                    raise ProbeError("Server requested authentication or another unsupported action; stopped")
                continue  # Ignore notifications; never print them or merge sparse state.
            if response.get("id") != self.counter:
                continue
            if "error" in response:
                error = response["error"]
                code = error.get("code") if isinstance(error, dict) else None
                raise ProbeError("Official read-only method failed", code if type(code) is int else None)
            return response.get("result")
        raise ProbeError("Read-only AppServer call timed out")

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=3)
        for handle in (self.process.stdin, self.process.stdout):
            handle.close()


def safe_number(value):
    return value if type(value) in (int, float) and math.isfinite(value) else None


def identity_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()[:16] if isinstance(value, str) and value else None


def safe_identifier(value):
    return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_./:-]{1,100}", value) else None


def boolean(value):
    return value if type(value) is bool else None


def credits_zero(credits):
    if not isinstance(credits, dict) or credits.get("hasCredits") is not False or credits.get("unlimited") is not False:
        return None
    try:
        value = Decimal(str(credits.get("balance")))
        return value == 0 if value.is_finite() else None
    except InvalidOperation:
        return None


def sanitized_limits(result):
    if not isinstance(result, dict):
        return {"available": False, "complete": False}
    buckets = result.get("rateLimitsByLimitId")
    if not isinstance(buckets, dict):
        legacy = result.get("rateLimits")
        buckets = {"legacy": legacy} if isinstance(legacy, dict) else {}
    output = []
    complete = bool(buckets) and len(buckets) <= 16
    for identifier, bucket in list(buckets.items())[:16]:
        if not isinstance(bucket, dict) or safe_identifier(identifier) is None:
            complete = False
            continue
        windows = []
        for name in ("primary", "secondary"):
            window = bucket.get(name)
            if isinstance(window, dict):
                windows.append({"name": name, "used_percent": safe_number(window.get("usedPercent")),
                                "duration_minutes": safe_number(window.get("windowDurationMins")),
                                "resets_at_unix": safe_number(window.get("resetsAt"))})
            elif window is not None:
                complete = False
        output.append({"bucket": identifier, "windows": windows,
                       "ordinary_usage_allowed": boolean(bucket.get("ordinaryUsageAllowed", result.get("ordinaryUsageAllowed"))),
                       "account_identity_hash": identity_hash(bucket.get("accountId", result.get("accountId"))),
                       "purchased_credit_balance_zero": credits_zero(bucket.get("credits")),
                       "auto_reload_enabled": boolean(bucket.get("autoReloadEnabled", result.get("autoReloadEnabled"))),
                       "purchased_credit_details_present": isinstance(bucket.get("credits"), dict)})
    return {"available": bool(output), "complete": complete, "buckets": output,
            "ordinary_usage_allowed": boolean(result.get("ordinaryUsageAllowed")),
            "account_identity_hash": identity_hash(result.get("accountId"))}


def probe(codex_home=None):
    client = None
    report = {"observed_at": iso(time.time()), "mode": "read_only", "model_requests_sent": 0,
              "account_read": "not_attempted", "limits_read": "not_attempted", "models_read": "not_attempted"}
    if not codex_home:
        report["blocker"] = "Specify a separate account home; default personal context is never selected"
        return report
    try:
        client = ReadOnlyClient(codex_home)
        client.call("initialize", {"clientInfo": {"name": "codex_usage_optimizer", "version": "0.2.0"},
                                   "capabilities": {"explicitGatewayOauth": True}})
        client.send({"method": "initialized"})
        result = client.call("account/read", {"refreshToken": False})
        account = result.get("account") if isinstance(result, dict) else None
        report["account_read"] = "completed"
        if not isinstance(account, dict) or account.get("type") != "chatgpt":
            raise ProbeError("Selected context is not a ChatGPT subscription; sign in separately with official Codex")
        report.update(account_type="chatgpt", account_identity_hash=identity_hash(account.get("accountId")))
        limits = client.call("account/rateLimits/read", {"excludeResetCreditDetails": True})
        report.update(limits_read="completed", limits=sanitized_limits(limits))
        models = client.call("model/list", {"limit": 100, "includeHidden": False})
        rows = models.get("data") if isinstance(models, dict) else None
        if not isinstance(rows, list):
            raise ProbeError("Model list unavailable")
        ids = [safe_identifier(row.get("model")) for row in rows[:100] if isinstance(row, dict)]
        report.update(models_read="completed", model_ids=[value for value in ids if value],
                      models_complete=len(rows) <= 100 and len(ids) == len(rows) and all(ids)
                      and models.get("nextCursor") is None)
        report["blocker"] = "Live dispatch disabled; auto reload and fixed-timer evidence require separate verification; activity is unknown"
    except (OSError, ValueError, TypeError, AttributeError, subprocess.SubprocessError, ProbeError) as error:
        report["blocker"] = error.reason if isinstance(error, ProbeError) else "Read-only client could not start or parse supported protocol"
        if isinstance(error, ProbeError):
            report["error_code"] = error.code
    finally:
        if client:
            client.close()
    return report


def status_from_report(alias, expected_hash, report):
    """Connect official metadata to the planner; never promote unknown activity."""
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{16}", expected_hash):
        return None
    limits = report.get("limits", {})
    if (report.get("account_type") != "chatgpt" or not limits.get("complete")
            or limits.get("account_identity_hash") != expected_hash
            or limits.get("ordinary_usage_allowed") is not True or not report.get("models_complete")):
        return None
    account_hash = report.get("account_identity_hash")
    if account_hash is not None and account_hash != expected_hash:
        return None
    windows = []
    zero, reload = [], []
    try:
        for bucket in limits["buckets"]:
            if bucket["account_identity_hash"] != expected_hash or bucket["ordinary_usage_allowed"] is not True or not bucket["windows"]:
                return None
            for window in bucket["windows"]:
                duration, used = window["duration_minutes"], window["used_percent"]
                if type(duration) is not int or duration <= 0 or type(used) not in (float, int) or not 0 <= used <= 100:
                    return None
                # Duration, never primary/secondary ordering, determines window identity.
                windows.append(Window(f'{bucket["bucket"]}:{duration}', used, timestamp(window["resets_at_unix"]), duration))
            zero.append(bucket["purchased_credit_balance_zero"])
            reload.append(bucket["auto_reload_enabled"])
        if not windows or len(windows) > 16 or len({window.key for window in windows}) != len(windows):
            return None
        return Status(alias, timestamp(report["observed_at"]), tuple(windows), tuple(report["model_ids"]), True, True,
                      True if all(value is True for value in zero) else None,
                      False if all(value is False for value in reload) else None,
                      None, False)
    except (ValueError, KeyError, TypeError):
        return None


class OfficialStatusAdapter:
    def __init__(self, codex_home, expected_hash):
        self.codex_home, self.expected_hash = codex_home, expected_hash
        self.report = None

    def read(self, alias):
        self.report = probe(self.codex_home)
        return status_from_report(alias, self.expected_hash, self.report)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", required=True)
    args = parser.parse_args()
    result = probe(args.codex_home)
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result.get("models_read") == "completed" and result.get("limits_read") == "completed" else 2)
