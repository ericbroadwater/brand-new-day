# Brand New Day

A Claude Code skill that automates the daily grind of finding, evaluating, and surfacing relevant job listings. Searches job boards by title keyword, scores every listing against your profile, and drops a local HTML dashboard with the high-fit matches each morning.

It replaces the 1–2 hour daily workflow of opening email digests, clicking through listings, and pasting JDs into Claude for evaluation. It does **not** auto-apply — it finds, scores, and surfaces. You decide what to pursue.

> **Status:** Alpha. Shipping calibrated for a Product Manager search, built by a PM (me) during an active job hunt. The rubric is tunable via config, but non-PM users will need to rewrite scoring prompts to match their role.

---

## What it does

1. Pulls live postings from the JSearch API (Google Jobs index) by title keyword
2. Dedupes against everything it has seen before
3. Scores each new listing on 10 weighted dimensions against your profile
4. Regenerates a local HTML dashboard with scored cards, apply links, and a full audit log
5. Runs overnight on cron so your morning starts with a fresh triage surface

Everything happens locally. No data leaves your machine except the JSearch API call (using your own key).

---

## Prerequisites

- **macOS** (Linux/Windows parity not yet supported)
- **[Claude Code](https://docs.claude.com/en/docs/claude-code/overview)** installed
- **Node.js 20+** (for the optional Playwright fallback renderer)
- **Python 3.9+** (stdlib only — no pip installs)
- **[RapidAPI account](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)** with a JSearch subscription (free tier: 200 requests/month)

---

## Install

```bash
git clone https://github.com/YOUR_USERNAME/brand-new-day.git
cd brand-new-day
./install.sh         # stub for now — prints manual steps
```

The real installer lands in Phase 1.5d. Until then, `install.sh` prints the manual sequence. The short version:

```bash
# 1. Pick a runtime home
export BND_HOME=~/brand-new-day
mkdir -p $BND_HOME/data

# 2. Copy runtime files
cp -r runtime/* $BND_HOME/
mv $BND_HOME/config.yml.example $BND_HOME/config.yml
mv $BND_HOME/profile.md.example $BND_HOME/profile.md
mv $BND_HOME/dashboard-template.html $BND_HOME/dashboard.html

# 3. Install the skill
cp -r skill ~/.claude/skills/brand-new-day

# 4. Configure secrets
cp .env.example $BND_HOME/.env
# Edit $BND_HOME/.env — set RAPIDAPI_KEY

# 5. (Optional) enable the pre-commit secret guard
git config core.hooksPath .githooks
```

Add `export BND_HOME=~/brand-new-day` to your shell profile (`~/.zshrc` or `~/.bash_profile`) so it persists across sessions.

---

## Customize

Two files, no code:

### `$BND_HOME/config.yml`

- `keywords.titles` — job titles to search (default: Product Manager variants)
- `keywords.locations` — your cities
- `keywords.exclude_titles` — titles the scanner should reject on sight
- `scoring.weights` — tune how much each dimension contributes
- `scoring.dimensions` — the 10-dimension rubric (name, weight, score-5/3/1 anchors)
- `scoring.hard_gates` — filters that force a score of 0 (default: `location_fit`)
- `scoring.threshold` — minimum composite score to surface on the dashboard
- `scheduling.operations_budget` — max tool calls per run

### `$BND_HOME/profile.md`

Your career context. The scoring engine reads this to decide what "a strong match" means for you. Sections: Background, Target Role, Hard Requirements, Nice-to-Haves, Comp Floor, Locations, Disqualifiers. See `profile.md.example` for the template.

**Changing target role = editing these two files.** No skill code touches required.

---

## Run

**Manual:**

```
/brand-new-day              # Full scan + score + dashboard regeneration
/brand-new-day review       # Mark listings as reviewed from the CLI
/brand-new-day status       # Show last run summary
/brand-new-day rescore      # Re-score all unreviewed listings (after config change)
```

Open `$BND_HOME/dashboard.html` in a browser for the visual view.

---

## Cron (overnight scans)

Two supported paths. Pick whichever matches your setup.

### Option A — `mcp__scheduled-tasks` (if you have that MCP)

If you run the [`scheduled-tasks` MCP server](https://github.com/anthropics/mcp-servers), schedule a task that invokes `/brand-new-day` overnight. In the MCP's UI or config:

- Schedule: `0 0 * * *` (midnight daily) — or whatever fits your credit window
- Command: `/brand-new-day`
- Working directory: your BND_HOME or project root

### Option B — `launchd` (macOS fallback)

Save as `~/Library/LaunchAgents/com.brandnewday.scan.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.brandnewday.scan</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/claude</string>
        <string>--headless</string>
        <string>/brand-new-day</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>0</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/brand-new-day.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/brand-new-day.err</string>
</dict>
</plist>
```

Load: `launchctl load ~/Library/LaunchAgents/com.brandnewday.scan.plist`

Adjust the `claude` binary path to match your install (`which claude`).

Linux `cron` and `systemd timer` variants are a stretch goal for a later release.

---

## Troubleshooting

**Permission prompts on every scan step.** The scan procedure uses helper scripts (`bnd-scan.py`, `bnd-hash.py`, `bnd-render-dashboard.py`) plus Claude native Read/Write/Edit tools precisely to avoid this. If you see a flood of prompts, you're probably running a modified scan flow that uses inline `python3 -c` or heredocs — those can't be pattern-permitted. See `skill/SKILL.md` Required Permissions.

**`RAPIDAPI_KEY` not found.** Check `$BND_HOME/.env` exists and has `RAPIDAPI_KEY=...` (no quotes, no trailing whitespace). `echo $BND_HOME` should match the directory you put `.env` in.

**JSearch returns 500 errors.** The `date_posted=today` filter is broken upstream. Use `week` or `3days`. Already the default in `config.yml.example`.

**`remote_jobs_only` doesn't filter.** Confirmed broken upstream (2026-04-15). The shipped query strategy appends `"remote"` to the query text instead — see `config.yml → api_budget.query_strategy`.

**Rate limit hit.** JSearch free tier is 200 requests/month. Default is 4 queries/run × 30 days = 120 req/month, leaving headroom. If you add keywords, watch `data/api-usage.json`.

**Dashboard shows no listings after a run.** Check `data/listings.json` and `data/run-log.json`. If they're populated but the dashboard is stale, run `/brand-new-day` again — dashboard regenerates from data files every time.

---

## Security

**Read this before pushing your fork anywhere.**

1. **Reset `.env` on every fork.** Your RapidAPI key lives there. `.env` is gitignored, but if you copied one from an old clone, delete it and start fresh.
2. **Your profile is personal data.** `profile.md` is gitignored. Never commit it. Never PR it. Never paste it into a public issue.
3. **Your listings are also personal data.** `data/listings.json`, `reviewed.json`, `dashboard.html` all reveal what roles you're watching. All gitignored. Keep them that way.
4. **Enable the pre-commit hook.** `git config core.hooksPath .githooks` installs a local hook that greps staged diffs for common API key patterns and blocks the commit if any hit.
5. **Verify before first push.** After setting up your fork:
   ```bash
   git log --all -p | grep -iE "rapidapi|x-rapidapi-key|AKIA"    # must return nothing
   git status                                                     # must not list .env, profile.md, or any data/*.json
   ```

The repo ships with no real listings, no real profile, no real `.env`. Fresh clones are clean. It's on you to keep your fork that way.

---

## Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Scheduler   │───▶│   Search     │───▶│   Scoring    │
│ cron/manual  │    │  JSearch API │    │   Claude     │
└──────────────┘    └──────────────┘    └──────────────┘
                                                │
                           ┌────────────────────┴─────────────────┐
                           ▼                                      ▼
                  ┌──────────────┐                       ┌──────────────┐
                  │  Data layer  │                       │  Dashboard   │
                  │ listings.json│                       │ HTML, light  │
                  │ reviewed.json│                       │ card-based   │
                  └──────────────┘                       └──────────────┘
```

- **Search:** JSearch returns structured JSON of live postings. No URL scraping, no stale results.
- **Scoring:** Claude reads the JD text and scores against your profile on 10 dimensions. No ML model, no external service — same thing you'd do by hand, automated.
- **Dedup:** Normalized hash of `company + title + location`. Cross-platform duplicates collapse to one entry.
- **Dashboard:** Single self-contained HTML file. Regenerated from scratch on every run. Light mode, card-based, print-friendly.

Full architecture spec: [PRD v1.5](./docs/PRD-v1.5.md) ([reading guide](./docs/PRD-v1.5-reading-guide.md)).

---

## What's NOT in this alpha

- **LinkedIn scraping** — TOS risk. Stays manual.
- **Auto-apply** — out of scope. This is a triage tool, not an application bot.
- **Cover letter generation** — planned for Phase 2.
- **Interview-prep handoff** — planned for Phase 2.
- **Non-PM rubric templates** — ships calibrated for PM; other roles need config edits.
- **Windows/Linux install parity** — macOS only for alpha.

---

## License

MIT. See [LICENSE](./LICENSE).

---

## About

Built by [Eric Broadwater](https://technicaldebt.me) as part of an active job search. The repo itself is a portfolio artifact — if you're a hiring manager who ended up here, the thing you're looking at is the kind of system I build: small, practical, automated where automation buys leverage, manual where manual is honest.
