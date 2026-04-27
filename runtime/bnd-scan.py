#!/usr/bin/env python3
"""
bnd-scan.py — Brand New Day JSearch API query runner.

Invokes the JSearch API (via RapidAPI) for a single query, returns parsed
JSON results to stdout. Replaces the `curl | python3 -c` pattern that
cannot be pattern-permitted in Claude Code.

REQUIRED PERMISSION PATTERNS (add to .claude/settings.local.json):
    Bash(python3 brand-new-day/bnd-scan.py:*)
    Bash(python3 /absolute/path/to/brand-new-day/bnd-scan.py:*)

DO NOT PIPE the output of this script into python3 -c, jq, head, or any
other command. The script returns parsed JSON — consume it directly,
redirect to a file, or read the output as a whole. Piping reintroduces
the variable-inline-code problem this script was built to solve.

Usage:
    python3 brand-new-day/bnd-scan.py --query "Product Manager remote"
    python3 brand-new-day/bnd-scan.py --query "Director of Product remote" \\
        --date-posted week --num-pages 1

Exit codes:
    0  success
    2  API error (non-200, malformed response)
    3  rate limit hit (HTTP 429 or monthly cap reached)
    4  missing RAPIDAPI_KEY in .env
    5  network/timeout error

Environment:
    Reads RAPIDAPI_KEY from $BND_HOME/.env, or ~/Claude/Jobs/brand-new-day/.env
    if BND_HOME is unset.

Dependencies: Python 3 stdlib only. No pip installs required.
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

API_HOST = "jsearch.p.rapidapi.com"
API_URL = f"https://{API_HOST}/search"
TIMEOUT_SECONDS = 30


def resolve_env_path() -> Path:
    """Find the .env file. Prefer $BND_HOME, fall back to known default."""
    bnd_home = os.environ.get("BND_HOME")
    if bnd_home:
        return Path(bnd_home) / ".env"
    return Path.home() / "Claude" / "Jobs" / "brand-new-day" / ".env"


def load_api_key(env_path: Path) -> str:
    """Parse .env, return RAPIDAPI_KEY. Exits 4 if missing."""
    if not env_path.exists():
        print(f"ERROR: .env not found at {env_path}", file=sys.stderr)
        sys.exit(4)

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "RAPIDAPI_KEY":
            return value.strip().strip('"').strip("'")

    print(f"ERROR: RAPIDAPI_KEY not set in {env_path}", file=sys.stderr)
    sys.exit(4)


def call_jsearch(query: str, date_posted: str, num_pages: int, api_key: str) -> dict:
    """Call JSearch, return parsed JSON. Exits on error."""
    params = urllib.parse.urlencode({
        "query": query,
        "num_pages": str(num_pages),
        "date_posted": date_posted,
    })
    url = f"{API_URL}?{params}"
    req = urllib.request.Request(url, headers={
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": API_HOST,
    })

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"ERROR: rate limit (HTTP 429): {e.reason}", file=sys.stderr)
            sys.exit(3)
        print(f"ERROR: HTTP {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(2)
    except urllib.error.URLError as e:
        print(f"ERROR: network/timeout: {e.reason}", file=sys.stderr)
        sys.exit(5)

    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON response: {e}", file=sys.stderr)
        sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a single JSearch API query and emit parsed JSON to stdout.",
    )
    parser.add_argument("--query", required=True, help='e.g. "Product Manager remote"')
    parser.add_argument("--date-posted", default="week", choices=["today", "3days", "week", "month", "all"],
                        help="JSearch date_posted filter. 'today' returns 500 — use 'week' or '3days'.")
    parser.add_argument("--num-pages", type=int, default=1, help="Pages (10 results each). 1 = 10 results = 1 API call.")
    args = parser.parse_args()

    api_key = load_api_key(resolve_env_path())
    result = call_jsearch(args.query, args.date_posted, args.num_pages, api_key)

    if result.get("status") != "OK":
        print(f"ERROR: API status not OK: {result.get('status')} — {result.get('error', {})}",
              file=sys.stderr)
        sys.exit(2)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
