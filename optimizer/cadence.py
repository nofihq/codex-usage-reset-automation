"""Persisted metadata read cadence; no model, network or scheduler operations."""
from dataclasses import asdict
import hashlib
import json
import math

MAX_FAILURES = 8
MAX_BACKOFF = 12*3600
MAX_INTERVAL = 30*86400


def fingerprint(profile, policy, expected_hash):
    value={'profile':asdict(profile),'policy':asdict(policy),'identity':expected_hash}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def due(account, now, config_hash, force=False):
    if force or account.get('read_config_hash') != config_hash:
        return True
    deadline=account.get('next_status_read_at')
    if deadline is None:
        return True
    if type(deadline) not in (int,float) or not math.isfinite(deadline) or not 0 < deadline < 32503680000:
        raise ValueError('Invalid read deadline')
    return now >= deadline


def record(account, decision, status_available, now, policy, config_hash):
    failures=account.get('read_failures',0)
    if type(failures) is not int or not 0 <= failures <= MAX_FAILURES:
        raise ValueError('Invalid metadata failure count')
    if status_available:
        failures=0
        next_at=min(now+MAX_INTERVAL,max(now+60,decision.next_check_at))
    else:
        failures=min(MAX_FAILURES,failures+1)
        next_at=now+min(MAX_BACKOFF,policy.unknown_recheck_seconds*2**(failures-1))
    account.update(read_failures=failures,next_status_read_at=next_at,read_config_hash=config_hash)
    return next_at


def health_transition(account, available):
    previous=account.get('read_health')
    current='ready' if available else 'blocked'
    account['read_health']=current
    if current == 'blocked' and previous != 'blocked':
        return 'account_check_blocked'
    if current == 'ready' and previous == 'blocked':
        return 'account_check_recovered'
    return None
