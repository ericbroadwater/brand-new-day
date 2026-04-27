#!/usr/bin/env python3
"""Regenerate brand-new-day dashboard.html from data files.

Usage:
    python3 brand-new-day/bnd-render-dashboard.py

Reads:   data/listings.json, data/run-log.json, dashboard.html
Writes:  dashboard.html — LISTINGS array + RUN_LOG object replaced.
         All CSS, HTML structure, and JS logic outside those two blocks
         is preserved verbatim.

Permission pattern for clean runs (add to .claude/settings.local.json):
    Bash(python3 brand-new-day/bnd-render-dashboard.py:*)
    Bash(python3 /absolute/path/to/brand-new-day/bnd-render-dashboard.py:*)
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Maps listings.json dimension keys → dashboard display labels.
# location_fit and comp_signals are intentionally omitted (shown via
# locationFail flag and salary badge respectively).
DIM_MAP = [
    ("seniority_fit",          "Seniority"),
    ("domain_match",           "Domain"),
    ("growth_plg",             "Growth/PLG"),
    ("platform_architecture",  "Platform"),
    ("company_stage",          "Stage"),
    ("role_clarity",           "Clarity"),
    ("people_management",      "People Mgmt"),
    ("application_friction",   "Friction"),
]
THRESHOLD = 3.5


def fmt_posted(iso):
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        # %-d is a Linux/macOS convention for un-padded day
        return dt.strftime("Posted %b %-d, %Y")
    except Exception:
        return ""


def render_listing(entry):
    scores = entry.get("scores") or {}
    composite = scores.get("composite", 0) or 0
    dims_raw = scores.get("dimensions") or {}
    loc = dims_raw.get("location_fit") or {}
    location_fail = (loc.get("gate") == "fail")

    if location_fail or composite < THRESHOLD:
        dims_out = []
    else:
        dims_out = []
        for key, display in DIM_MAP:
            d = dims_raw.get(key)
            if not d:
                continue
            dims_out.append({
                "n": display,
                "s": d.get("score", 0),
                "note": d.get("note", ""),
            })

    return {
        "id":           entry.get("id", ""),
        "title":        entry.get("title", ""),
        "company":      entry.get("company", ""),
        "location":     entry.get("location", ""),
        "score":        composite,
        "comp":         entry.get("comp_range") or "",
        "source":       entry.get("source", ""),
        "posted":       fmt_posted(entry.get("posting_date")),
        "partial":      bool(entry.get("partial_data", False)),
        "locationFail": location_fail,
        "url":          entry.get("apply_url") or entry.get("url", ""),
        "discoveredAt": entry.get("discovered_at", ""),
        "summary":      scores.get("fit_summary", ""),
        "dims":         dims_out,
    }


_IDENT_KEY = re.compile(r'^(\s*)"([a-zA-Z_][a-zA-Z0-9_]*)":', flags=re.MULTILINE)


def js_pretty(obj, outer_indent=0):
    """Return a JS-literal pretty-print with unquoted simple-identifier keys.

    Values remain JSON-compatible (JS accepts JSON). The dashboard template
    uses unquoted keys, so matching that style keeps file diffs clean.
    """
    raw = json.dumps(obj, indent=2, ensure_ascii=False)
    raw = _IDENT_KEY.sub(r"\1\2:", raw)
    if outer_indent:
        pad = " " * outer_indent
        lines = raw.split("\n")
        raw = lines[0] + "\n" + "\n".join(pad + ln for ln in lines[1:])
    return raw


def build_listings_block(listings):
    ranked = sorted(
        listings,
        key=lambda e: -((e.get("scores") or {}).get("composite", 0) or 0),
    )
    rendered = [render_listing(e) for e in ranked]
    if not rendered:
        return "const LISTINGS = [];"
    items = []
    for obj in rendered:
        body = js_pretty(obj)
        body = "\n".join("  " + line for line in body.split("\n"))
        items.append(body)
    return "const LISTINGS = [\n" + ",\n".join(items) + "\n];"


def build_run_log_block(run_log):
    entry = run_log[-1] if run_log else {}
    obj = {
        "run_id":           entry.get("run_id", ""),
        "completed_at":     entry.get("completed_at", ""),
        "status":           entry.get("status", ""),
        "queries_executed": entry.get("queries_executed", 0),
        "listings_new":     entry.get("listings_new", 0),
        "notes":            entry.get("notes", ""),
    }
    return f"const RUN_LOG = {js_pretty(obj)};"


def main():
    bnd_home = Path(__file__).resolve().parent
    dashboard_path = bnd_home / "dashboard.html"
    listings_path  = bnd_home / "data" / "listings.json"
    run_log_path   = bnd_home / "data" / "run-log.json"

    listings = json.loads(listings_path.read_text(encoding="utf-8"))
    run_log  = json.loads(run_log_path.read_text(encoding="utf-8"))
    html     = dashboard_path.read_text(encoding="utf-8")

    new_listings = build_listings_block(listings)
    new_run_log  = build_run_log_block(run_log)

    # Use lambda replacements so backslashes in the content aren't interpreted.
    html, n1 = re.subn(
        r"const LISTINGS = \[[\s\S]*?\n\];",
        lambda m: new_listings,
        html,
        count=1,
    )
    if n1 != 1:
        print("ERROR: could not locate LISTINGS array in dashboard.html", file=sys.stderr)
        sys.exit(3)

    html, n2 = re.subn(
        r"const RUN_LOG = \{[\s\S]*?\n\};",
        lambda m: new_run_log,
        html,
        count=1,
    )
    if n2 != 1:
        print("ERROR: could not locate RUN_LOG object in dashboard.html", file=sys.stderr)
        sys.exit(4)

    dashboard_path.write_text(html, encoding="utf-8")

    total = len(listings)
    above = sum(
        1 for e in listings
        if ((e.get("scores") or {}).get("composite", 0) or 0) >= THRESHOLD
    )
    print(f"Dashboard updated: {total} listings ({above} above threshold).")


if __name__ == "__main__":
    main()
