#!/usr/bin/env python3
"""Check a fresh local clone without sign-in, network access or cloud actions."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


def run(command, cwd, env=None, test_output=False):
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                            text=True, encoding="utf-8", timeout=60)
    if result.returncode:
        if test_output:
            # This suite uses synthetic identities and empty homes only.
            print(result.stderr[-12000:], file=sys.stderr)
        raise RuntimeError("Repository check failed: " + Path(command[0]).name)
    return result


def anchors(text):
    result, counts, fenced = set(), {}, False
    for line in text.splitlines():
        if line.startswith(("```", "~~~")):
            fenced = not fenced
        if fenced:
            continue
        match = re.match(r"^#{1,6} +(.+?) *#* *$", line)
        if not match:
            continue
        title = match.group(1).lower().replace("`", "")
        slug = "".join(c for c in title if not unicodedata.category(c).startswith("P") or c in "-_")
        slug = slug.replace(" ", "-")
        count = counts.get(slug, 0)
        result.add(slug + ("-" + str(count) if count else ""))
        counts[slug] = count + 1
    return result


def check_documents(root, names):
    root, errors, checked = Path(root).resolve(), [], 0
    for name in names:
        if not name.endswith(".md"):
            continue
        path = root / name
        text = path.read_text(encoding="utf-8")
        for value in re.findall(r"\]\(([^\s)]+)\)", text):
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", value):
                continue
            checked += 1
            location, _, anchor = value.partition("#")
            target = (path.parent / location).resolve() if location else path
            try:
                target.relative_to(root)
            except ValueError:
                errors.append(name + ": link leaves repository")
                continue
            if not target.is_file():
                errors.append(name + ": missing link target " + location)
            elif anchor and target.suffix == ".md" and anchor not in anchors(target.read_text(encoding="utf-8")):
                errors.append(name + ": missing heading " + anchor)
    return {"internal_links": checked, "errors": errors}


def main():
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory(prefix="cloud-setup-check-") as temp:
        clone = Path(temp) / "source"
        run(["git", "clone", "--no-hardlinks", "--quiet", str(ROOT), str(clone)], ROOT, env)
        names = run(["git", "ls-files"], clone, env).stdout.splitlines()
        documents = check_documents(clone, names)
        if documents["errors"]:
            print(json.dumps({"ok": False, **documents}, indent=2))
            return 2
        run([sys.executable, "scripts/privacy_check.py"], clone, env)
        tests = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], clone, env, test_output=True)
        count = re.search(r"Ran (\d+) tests", tests.stderr)
        skipped = re.search(r"OK \(skipped=(\d+)\)", tests.stderr)
        tests_run = int(count.group(1)) if count else None
        tests_skipped = int(skipped.group(1)) if skipped else 0
        clean = not run(["git", "status", "--porcelain"], clone, env).stdout.strip()
        print(json.dumps({"ok": clean, "checks": ["fresh local clone", "internal Markdown links and headings",
              "tracked-source privacy scan", "repository check regression tests", "clean working tree"],
              "internal_links": documents["internal_links"], "tests_run": tests_run,
              "tests_passed": tests_run - tests_skipped if tests_run is not None else None,
              "tests_skipped": tests_skipped,
              "network_calls": 0, "account_reads": 0, "model_requests": 0}, indent=2))
        return 0 if clean else 2


if __name__ == "__main__":
    raise SystemExit(main())
