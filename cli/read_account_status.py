#!/usr/bin/env python3
"""Metadata-only status reader; Python 3.10+, Windows, macOS and Linux.

Pass --binary, --home, --runtime and --expectations-fd explicitly. The FD must
refer to a private, owner-controlled regular JSON file containing expectedEmail.
Requires the installed app-server's experimental account/read response field
workspaceRouting.chatgptAccountId (at the result root, alongside account).
This independently obtained authenticated routing ID must match the subsequent
usage accountId. Missing or mismatched identity/binding always holds. The stable
email-only account schema is insufficient; never bootstrap a binding from usage.
No expected identity, account ID, server text or raw error is output.
No credentials are read by this script; the explicitly selected app-server
uses its existing CODEX_HOME. No login, refresh, thread or inference is requested.
"""

import argparse
import datetime
import json
import math
import os
from pathlib import Path
import re
import platform
import queue
import stat
import subprocess
import sys
import tempfile
import threading
import time


class Hold(Exception):
    pass


PLANS = set("free go plus pro prolite promax team self_serve_business_prolite self_serve_business_usage_based business ent26 enterprise_cbp_automation enterprise_cbp_usage_based enterprise edu edu_plus edu_pro unknown".split())
SUPPORTED_VERSION = "0.159.2"


def parse_json(raw, reason):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise Hold("duplicate_json_key")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=unique)
    except (ValueError, UnicodeError, RecursionError):
        raise Hold(reason) from None


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate_expectations(value):
    if not isinstance(value, dict):
        raise Hold("invalid_expectations")
    if not nonempty(value.get("expectedEmail")):
        raise Hold("missing_expected_identity")
    return value


def read_expectations(fd):
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_size > 8192:
        raise Hold("unsafe_expectations_file")
    if os.name == "nt":
        import msvcrt
        windows_security().validate_private(handle=msvcrt.get_osfhandle(fd))
    elif info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise Hold("unsafe_expectations_file")
    raw = os.read(fd, 8193)
    if len(raw) > 8192:
        raise Hold("invalid_expectations")
    return validate_expectations(parse_json(raw, "invalid_expectations"))


def windows_security():
    if __package__:
        from . import windows_security as security
    else:
        import windows_security as security
    return security


def private_directory(path, create=False):
    path = Path(path)
    if create and not path.exists():
        if os.name == "nt":
            windows_security().create_private_directory(path)
        else:
            path.mkdir(mode=0o700)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise Hold("unsafe_private_directory")
    if os.name == "nt":
        windows_security().validate_private(path)
    elif info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise Hold("unsafe_private_directory")
    return path


def native_binary(prefix):
    systems = {"Linux": ("linux", "unknown-linux-musl"),
               "Darwin": ("darwin", "apple-darwin"),
               "Windows": ("win32", "pc-windows-msvc")}
    arches = {"amd64": ("x64", "x86_64"), "x86_64": ("x64", "x86_64"),
              "arm64": ("arm64", "aarch64"), "aarch64": ("arm64", "aarch64")}
    if platform.system() not in systems or platform.machine().lower() not in arches:
        raise Hold("unsupported_platform")
    system, target = systems[platform.system()]
    arch, vendor_arch = arches[platform.machine().lower()]
    package = "codex-" + system + "-" + arch
    root = Path(prefix).absolute() / "node_modules" / "@openai"
    tail = Path("vendor") / (vendor_arch + "-" + target) / "bin" / ("codex.exe" if system == "win32" else "codex")
    for parent in (root, root / "codex" / "node_modules" / "@openai"):
        binary = parent / package / tail
        if binary.is_file():
            return str(binary)
    raise Hold("official_native_binary_missing")


class MetadataClient:
    ALLOWED = {"initialize", "account/read", "account/rateLimits/read", "model/list"}

    def __init__(self, binary, home, runtime, timeout):
        self.timeout, self.next_id, self.buffer = timeout, 0, b""
        for path in (binary, home, runtime):
            if not Path(path).is_absolute():
                raise Hold("paths_must_be_absolute")
        private_directory(runtime)
        private_directory(home)
        if Path(binary).suffix.lower() in {".cmd", ".bat", ".ps1", ".js"}:
            raise Hold("native_binary_required")
        env = os.environ.copy()
        for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN",
                    "OPENAI_ACCESS_TOKEN", "OPENAI_BASE_URL", "OPENAI_API_BASE",
                    "OPENAI_ORG_ID", "OPENAI_PROJECT_ID", "OPENAI_ORGANIZATION",
                    "OPENAI_PROJECT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT",
                    "AZURE_OPENAI_AD_TOKEN", "OPENAI_FEDERATION_RULE_ID",
                    "OPENAI_IDENTITY_TOKEN_FILE", "OPENAI_WORKLOAD_IDENTITY_CONTEXT",
                    "CODEX_REFRESH_TOKEN_URL_OVERRIDE"):
            env.pop(key, None)
        env.update(CODEX_HOME=home, XDG_RUNTIME_DIR=runtime)
        # Inspect the installed binary without opening the selected credential store.
        with tempfile.TemporaryDirectory(prefix="version-", dir=runtime) as empty_home:
            version = subprocess.run(
                [binary, "--version"], cwd=empty_home,
                env=dict(env, CODEX_HOME=empty_home), capture_output=True, timeout=10,
            )
        if version.returncode or version.stdout.strip() != ("codex-cli " + SUPPORTED_VERSION).encode():
            raise Hold("unsupported_cli_version")
        self.process = subprocess.Popen(
            [binary, "-c", 'forced_login_method="chatgpt"',
             "-c", 'cli_auth_credentials_store="file"',
             "app-server", "--listen", "stdio://"], env=env, cwd=home,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, close_fds=True,
        )
        self.messages = queue.Queue(maxsize=4)
        self.stopped = threading.Event()
        def read():
            try:
                while not self.stopped.is_set():
                    chunk = self.process.stdout.readline(1048577)
                    while not self.stopped.is_set():
                        try:
                            self.messages.put(chunk, timeout=0.1)
                            break
                        except queue.Full:
                            continue
                    if not chunk:
                        return
            except (OSError, ValueError):
                if not self.stopped.is_set():
                    try:
                        self.messages.put(b"", timeout=1)
                    except queue.Full:
                        pass
        self.reader = threading.Thread(target=read, daemon=True)
        self.reader.start()

    def send(self, message):
        self.process.stdin.write((json.dumps(message) + "\n").encode())
        self.process.stdin.flush()

    def initialized(self):
        self.send({"method": "initialized", "params": {}})

    def call(self, method, params):
        if method not in self.ALLOWED:
            raise Hold("non_metadata_method_blocked")
        self.next_id += 1
        request_id = self.next_id
        self.send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        total = len(self.buffer)
        while time.monotonic() < deadline:
            try:
                line = self.messages.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty:
                break
            if not line:
                raise Hold("server_closed")
            total += len(line)
            if total > 1048576:
                raise Hold("server_message_too_large")
            message = parse_json(line, "invalid_server_message")
            if not isinstance(message, dict):
                raise Hold("invalid_server_message")
            if "method" in message:
                if "id" in message:
                    raise Hold("unexpected_server_request")
                continue  # Discard notifications; never retain raw events.
            if type(message.get("id")) is not int:
                raise Hold("invalid_response_id")
            if message["id"] != request_id:
                continue
            if "error" in message:
                raise Hold("rpc_error")
            if not isinstance(message.get("result"), dict):
                raise Hold("invalid_rpc_result")
            return message["result"]
        raise Hold("rpc_timeout")

    def close(self):
        self.stopped.set()
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process.stdin.close()
        self.reader.join(timeout=2)
        if not self.reader.is_alive():
            self.process.stdout.close()
        else:
            raise OSError("Reader shutdown incomplete")


def number(value, minimum, maximum, integer=False):
    if value is None:
        return None
    allowed = (int,) if integer else (int, float)
    if type(value) not in allowed or not minimum <= value <= maximum:
        raise Hold("invalid_numeric_metadata")
    return value


def boolean(value):
    if value is not None and type(value) is not bool:
        raise Hold("invalid_boolean_metadata")
    return value


def plan(value):
    return value if isinstance(value, str) and value in PLANS else None


def sanitize_limit(value):
    """Whitelist metadata; missing fields stay explicitly unknown (null)."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Hold("invalid_usage_shape")
    output = {}
    for name in ("primary", "secondary"):
        window = value.get(name)
        if window is None:
            output[name] = None
            continue
        if not isinstance(window, dict):
            raise Hold("invalid_usage_shape")
        output[name] = {
            "usedPercent": number(window.get("usedPercent"), 0, 100),
            "windowDurationMins": number(window.get("windowDurationMins"), 1, 2147483647, True),
            "resetsAt": number(window.get("resetsAt"), 0, 253402300799, True),
        }
    output["planType"] = plan(value.get("planType"))
    credits = value.get("credits")
    output["credits"] = None
    if credits is not None:
        if not isinstance(credits, dict):
            raise Hold("invalid_usage_shape")
        balance = credits.get("balance")
        if isinstance(balance, str):
            if len(balance) > 40 or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", balance):
                raise Hold("invalid_credit_balance")
            balance = float(balance)
        output["credits"] = {
            "hasCredits": boolean(credits.get("hasCredits")),
            "unlimited": boolean(credits.get("unlimited")),
            "balance": number(balance, 0, 1e15),
        }
    return output


def sanitize_inventory(value):
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Hold("invalid_inventory_shape")
    output = {"availableCount": number(value.get("availableCount"), 0, 2147483647, True), "credits": None}
    rows = value.get("credits")
    if rows is not None:
        if not isinstance(rows, list):
            raise Hold("invalid_inventory_shape")
        output["credits"] = []
        for row in rows:
            if not isinstance(row, dict):
                raise Hold("invalid_inventory_shape")
            status = row.get("status")
            output["credits"].append({
                "status": status if status in ("available", "redeeming", "redeemed", "unknown") else None,
                "grantedAt": number(row.get("grantedAt"), 0, 253402300799, True),
                "expiresAt": number(row.get("expiresAt"), 0, 253402300799, True),
                "expiryKnown": row.get("expiresAt") is not None,
            })
    return output


def collect(client, expected, inventory=False):
    expected = validate_expectations(expected)
    client.call("initialize", {
        "clientInfo": {"name": "status_metadata_reader", "title": "Read-only usage check", "version": "1.0"},
        "capabilities": {"explicitGatewayOauth": True, "experimentalApi": True},
    })
    client.initialized()
    identity = client.call("account/read", {"refreshToken": False})
    account = identity.get("account")
    if not isinstance(account, dict) or account.get("type") != "chatgpt":
        raise Hold("missing_chatgpt_identity")
    if not nonempty(account.get("email")):
        raise Hold("missing_account_identity")
    if account["email"] != expected["expectedEmail"]:
        raise Hold("account_identity_mismatch")
    routing = identity.get("workspaceRouting")
    if not isinstance(routing, dict) or not nonempty(routing.get("chatgptAccountId")):
        raise Hold("missing_independent_account_binding")
    expected_binding = routing["chatgptAccountId"]
    usage = client.call("account/rateLimits/read", {
        "excludeResetCreditDetails": not inventory, "supportsLunaReserve": False,
    })
    if not nonempty(usage.get("accountId")):
        raise Hold("missing_usage_account_binding")
    if usage["accountId"] != expected_binding:
        raise Hold("usage_account_binding_mismatch")
    # Binding is verified BEFORE discarding accountId or publishing any usage.
    sanitized = {"rateLimits": sanitize_limit(usage.get("rateLimits")),
                 "ordinaryUsageAllowed": boolean(usage.get("ordinaryUsageAllowed")),
                 "rateLimitsByLimitId": {"codex": None}}
    buckets = usage.get("rateLimitsByLimitId")
    if buckets is not None:
        if not isinstance(buckets, dict):
            raise Hold("invalid_usage_shape")
        codex = buckets.get("codex")
        if isinstance(codex, dict) and codex.get("accountId", expected_binding) != expected_binding:
            raise Hold("usage_account_binding_mismatch")
        if isinstance(codex, dict) and codex.get("limitId") not in (None, "codex"):
            raise Hold("usage_limit_binding_mismatch")
        sanitized["rateLimitsByLimitId"]["codex"] = sanitize_limit(codex)
    legacy = usage.get("rateLimits")
    if isinstance(legacy, dict) and legacy.get("accountId", expected_binding) != expected_binding:
        raise Hold("usage_account_binding_mismatch")
    if isinstance(legacy, dict) and legacy.get("limitId") not in (None, "codex"):
        raise Hold("usage_limit_binding_mismatch")
    if inventory:
        sanitized["rateLimitResetCredits"] = sanitize_inventory(usage.get("rateLimitResetCredits"))
    models = client.call("model/list", {"includeHidden": False, "limit": 100})
    data = models.get("data")
    if (not isinstance(data, list) or len(data) > 100
            or any(not isinstance(row, dict) or not isinstance(row.get("model"), str)
                   or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,255}", row["model"])
                   for row in data)):
        raise Hold("invalid_model_list")
    cursor = models.get("nextCursor")
    if cursor is not None and (not nonempty(cursor) or len(cursor) > 8192):
        raise Hold("invalid_model_cursor")
    listed = any(isinstance(row, dict) and row.get("model") == "gpt-6-luna" for row in data)
    return {
        "state": "metadata_verified", "eligibility": "unknown",
        "checkedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "identityMatchesExpected": True, "usageBindingMatchesExpected": True,
        "planType": plan(account.get("planType")),
        "usage": sanitized,
        "luna": {"listedOnFirstPage": listed, "morePages": bool(models.get("nextCursor"))},
    }


def main():
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            raise Hold("invalid_arguments")

    parser = SafeParser(description=__doc__)
    parser.add_argument("--init-private", metavar="DIRECTORY")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--binary")
    source.add_argument("--tools", help="npm installation prefix; selects the native executable")
    for flag in ("home", "runtime"):
        parser.add_argument("--" + flag)
    identity = parser.add_mutually_exclusive_group()
    identity.add_argument("--expectations-fd", type=int)
    identity.add_argument("--expectations-file")
    parser.add_argument("--timeout", type=float, default=45)
    parser.add_argument("--inventory", action="store_true")
    client = None
    code = 2
    try:
        args = parser.parse_args()
        if args.init_private:
            root = Path(args.init_private).absolute()
            private_directory(root, create=True)
            private_directory(root / "plus", create=True)
            private_directory(root / "runtime", create=True)
            print(json.dumps({"state": "private_directories_ready"}))
            return 0
        if not math.isfinite(args.timeout) or not 0 < args.timeout <= 300:
            raise Hold("invalid_timeout")
        if not args.home or not args.runtime or not (args.binary or args.tools):
            raise Hold("missing_paths")
        if args.expectations_file:
            path = Path(args.expectations_file)
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise Hold("unsafe_expectations_file")
            fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            try:
                expected = read_expectations(fd)
            finally:
                os.close(fd)
        elif args.expectations_fd is not None:
            expected = read_expectations(args.expectations_fd)
        else:
            raise Hold("missing_expected_identity")
        binary = str(Path(args.binary).absolute()) if args.binary else native_binary(args.tools)
        client = MetadataClient(binary, str(Path(args.home).absolute()), str(Path(args.runtime).absolute()), args.timeout)
        output = collect(client, expected, args.inventory)
        code = 0
    except Hold as error:
        output = {"state": "hold", "reason": str(error)}
    except Exception:
        output = {"state": "hold", "reason": "local_or_protocol_error"}
    finally:
        if client is not None:
            try:
                client.close()
            except OSError:
                output = {"state": "hold", "reason": "cleanup_error"}
                code = 2
    print(json.dumps(output, allow_nan=False), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
