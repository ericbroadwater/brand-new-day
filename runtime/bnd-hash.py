#!/usr/bin/env python3
"""Compute 8-char dedup ID for a BND listing.

Usage:
    python3 brand-new-day/bnd-hash.py <company> <title> <location>

Prints the 8-char hex hash to stdout. Used by the scan flow to generate
dedup IDs without inline python invocations.

Permission pattern for clean runs (add to .claude/settings.local.json):
    Bash(python3 brand-new-day/bnd-hash.py:*)
    Bash(python3 /absolute/path/to/brand-new-day/bnd-hash.py:*)
"""
import hashlib
import sys


def main():
    if len(sys.argv) != 4:
        print("usage: bnd-hash.py <company> <title> <location>", file=sys.stderr)
        sys.exit(2)
    company, title, location = (a.strip().lower() for a in sys.argv[1:4])
    key = f"{company}|{title}|{location}"
    print(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8])


if __name__ == "__main__":
    main()
