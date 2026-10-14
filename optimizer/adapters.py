"""Read-only fixtures and a keyless public feed. No account authentication code."""
import hashlib
import json
import math
import re
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler

from .core import Event, Status, Window, timestamp

STATUS_BYTES = 65536
FEED_BYTES = 1048576  # Public archive is large; bounded RAM only, never saved raw.
FEED_ENDPOINT = "https://codex-reset.com/api/timeline"
SOURCE = "https://codex-reset.com/"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_json(path, limit):
    with Path(path).expanduser().open("rb") as handle:
        content = handle.read(limit + 1)
    if len(content) > limit:
        raise ValueError("Input exceeds byte limit")
    return json.loads(content, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite number")))


class SnapshotStatusAdapter:
    """Normalized adapter contract, NOT an invented OpenAI HTTP endpoint.

    A future official adapter must capability-detect identity and usage permission,
    validate ChatGPT subscription auth, and enumerate complete actual buckets.
    For this phase only explicit snapshot files are read. No credentials are read.
    """
    def __init__(self, path):
        self.path = path

    def read(self, account_id):
        try:
            payload = read_json(self.path, STATUS_BYTES)
            row = payload["accounts"].get(account_id)
            if not row or row.get("auth_kind") != "chatgpt":
                return None
            windows = []
            for bucket in row["windows"]:
                used = bucket["used_percent"]
                duration = bucket["duration_minutes"]
                key = bucket["key"]
                if (isinstance(used, bool) or not isinstance(used, (int, float))
                        or not math.isfinite(used) or not 0 <= used <= 100
                        or type(duration) is not int or duration <= 0
                        or not isinstance(key, str) or not 0 < len(key) <= 100):
                    return None
                windows.append(Window(key, used, timestamp(bucket["resets_at"]), duration))
            models = row.get("model_ids", [])
            if len(windows) > 16 or not isinstance(models, list) or len(models) > 100:
                return None
            if any(not isinstance(m, str) or len(m) > 100 for m in models):
                return None
            permission = row.get("ordinary_usage_allowed")
            if permission is not None and type(permission) is not bool:
                return None
            return Status(row["account_id"], timestamp(row["observed_at"]), tuple(windows),
                          tuple(models), row.get("verified") is True, permission,
                          row.get("purchased_credit_balance_zero") if type(row.get("purchased_credit_balance_zero")) is bool else None,
                          row.get("auto_reload_enabled") if type(row.get("auto_reload_enabled")) is bool else None,
                          row.get("active_work") if type(row.get("active_work")) is bool else None,
                          row.get("inactivity_verified") is True)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return None


def parse_timeline(payload, now):
    """Allowlisted fields only; text never becomes commands, prompts, or logs."""
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        raise ValueError("Unknown timeline shape")
    if len(payload["events"]) > 2048:
        raise ValueError("Too many events")
    parsed = []
    for row in payload["events"]:
        if not isinstance(row, dict):
            continue
        try:
            when = timestamp(row["announced_at"])
        except (KeyError, ValueError):
            continue
        if when > now or when < now - 30 * 86400:
            continue
        group, announcement = row.get("group"), row.get("announcement_state", "unknown")
        if group == "reset" and announcement == "announced":
            kind = "global_reset"
        elif group == "credits" or row.get("banked_grant") is True:
            kind = "banked_notice"  # grants/availability are not a personal balance
        else:
            continue
        confirmed = row.get("confirmed")
        if type(confirmed) is not bool:
            confirmed = None  # optional noncontract field: absence remains unknown
        identifier = str(row.get("id", ""))
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", identifier):
            continue
        parsed.append(Event(identifier, kind, when, SOURCE, confirmed,
                            announcement if announcement in {"announced", "unknown"} else "unknown"))
    return sorted(parsed, key=lambda e: (e.occurred_at, e.event_id))


def ingest_events(events, state, now):
    """First-run baseline, exact+semantic dedup, bounded notification ledger.

    Related announcements in the same UTC date/group are one refresh hint.
    This deliberately does NOT claim they are the same personal credit/reset.
    Old events cannot re-alert after retention eviction due to the watermark.
    """
    feed = state.setdefault("feed", {})
    baseline = not feed.get("initialized", False)
    seen = feed.get("seen", {})
    ledger = feed.get("notification_ledger", {})
    records = feed.get("records", {})
    watermark = feed.get("watermark", 0)
    new = []
    for e in events:
        semantic = hashlib.sha256(f"{e.source}|{e.kind}|{int(e.occurred_at // 86400)}".encode()).hexdigest()
        event_key = hashlib.sha256(f"{e.source}|{e.event_id}".encode()).hexdigest()
        if not baseline and e.occurred_at > watermark and event_key not in seen and semantic not in ledger:
            new.append(e)
        seen[event_key] = now
        ledger[semantic] = now
        records[event_key] = {"event_id": e.event_id, "kind": e.kind, "occurred_at": e.occurred_at,
                              "source": e.source, "confirmed": e.confirmed,
                              "announcement_state": e.announcement_state}
    feed["seen"] = dict(sorted(((k, v) for k, v in seen.items() if v > now - 30*86400),
                               key=lambda item: (item[1], item[0]))[-256:])
    feed["notification_ledger"] = dict(sorted(((k, v) for k, v in ledger.items() if v > now - 30*86400),
                                              key=lambda item: (item[1], item[0]))[-256:])
    feed["watermark"] = max([watermark] + [e.occurred_at for e in events])
    feed["records"] = dict(sorted(((k, v) for k, v in records.items() if v["occurred_at"] > now - 30*86400),
                                  key=lambda item: (item[1]["occurred_at"], item[0]))[-64:])
    feed["initialized"] = True
    return new


def retry_after(value, now):
    try:
        if value.strip().isdigit():
            return now + min(int(value), 7*86400)
        return max(now, parsedate_to_datetime(value).timestamp())
    except (AttributeError, TypeError, ValueError, OverflowError):
        return now + 3600


class TrackerAdapter:
    """Explicit opt-in GET only; no guessed URL, redirects or raw-history files."""
    def __init__(self, user_agent, interval=14400, opener=None):
        if not user_agent or len(user_agent) > 256 or "\n" in user_agent or "\r" in user_agent:
            raise ValueError("Project User-Agent required")
        if type(interval) is not int or not 60 <= interval <= 7*86400:
            raise ValueError("Feed interval must be 60 seconds to seven days")
        self.user_agent, self.interval = user_agent, interval
        self.opener = opener or build_opener(NoRedirect()).open

    def read(self, state, now):
        feed = state.setdefault("feed", {})
        if now < feed.get("fetch_after", 0):
            return [], "not_due"
        feed["fetch_after"] = now + self.interval
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        for header, key in (("If-None-Match", "etag"), ("If-Modified-Since", "last_modified")):
            if feed.get(key):
                headers[header] = feed[key]
        request = Request(FEED_ENDPOINT, headers=headers, method="GET")
        try:
            with self.opener(request, timeout=10) as response:
                if response.geturl() != FEED_ENDPOINT:
                    return [], "unexpected_redirect"
                raw = response.read(FEED_BYTES + 1)
                if len(raw) > FEED_BYTES:
                    return [], "too_large"
                cache = re.search(r"max-age=(\d+)", response.headers.get("Cache-Control", ""))
                if cache:
                    feed["fetch_after"] = max(feed["fetch_after"], now + int(cache.group(1)))
                for header, key in (("ETag", "etag"), ("Last-Modified", "last_modified")):
                    val = response.headers.get(header)
                    if val and len(val) <= 256 and "\n" not in val and "\r" not in val:
                        feed[key] = val
                checked = timestamp(response.headers.get("x-published-checked-at"))
                expires = timestamp(response.headers.get("x-published-expires-at"))
                feed["published_checked_at"] = checked
                feed["published_expires_at"] = expires
                if checked > now or expires < now or now - checked > 600:
                    return [], "stale"
                payload = json.loads(raw)
                return parse_timeline(payload, now), "ok"
        except HTTPError as error:
            if error.code == 429:
                feed["fetch_after"] = max(feed["fetch_after"], retry_after(error.headers.get("Retry-After"), now))
                return [], "rate_limited"
            if error.code == 304:
                return [], "not_modified"
            return [], "http_error"
        except (OSError, ValueError, TypeError):
            return [], "unavailable"
