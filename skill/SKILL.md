---
name: brand-new-day
description: >
  Automated job search pipeline that finds, scores, and surfaces job listings
  against a user profile. Use this skill when the user says /brand-new-day,
  "run the scanner", "find jobs", "check for new listings", or any variation of
  running a job search scan. Also triggers on sub-commands: /brand-new-day init,
  /brand-new-day doctor, /brand-new-day reset, /brand-new-day review,
  /brand-new-day status, /brand-new-day rescore, /brand-new-day prep [id].
---

# Brand New Day

## Overview

Brand New Day automates the daily job search workflow for a single user. It searches public job boards and ATS platforms by job title keywords, scores each listing against a configured user profile, and outputs a local HTML dashboard of high-scoring matches.

It replaces the 1-2 hour daily manual process of checking email digests, clicking through listings, and pasting JDs into Claude for evaluation.

**PRD:** `~/Claude/Jobs/PRDs/versions/brand-new-day-prd-v1.5.md`

## Invocation

| Command | What it does |
|---|---|
| `/brand-new-day` | Full scan: search → fetch → score → generate dashboard |
| `/brand-new-day init` | Validate a fresh install: config + BND_HOME + .env + JSearch test call |
| `/brand-new-day doctor` | Re-run the validator against an existing install. Reports anything broken |
| `/brand-new-day reset` | Archive current `data/` to `data/archive-{date}/` and re-create empty starters |
| `/brand-new-day review` | Interactive review of unreviewed listings |
| `/brand-new-day status` | Show last run summary + pending items |
| `/brand-new-day rescore` | Re-score all unreviewed listings (after config changes) |
| `/brand-new-day prep [id or company]` | Trigger interview-prep one-sheet from a stored listing |

## Configuration

**Path resolution:** Read `BND_HOME` from `$BND_HOME/.env` (or `~/Claude/Jobs/brand-new-day/.env` if unset). When loading `config.yml`, substitute `{BND_HOME}` placeholders with that value. All BND paths in this skill use `$BND_HOME` — never hardcode the install location.

All settings live in `$BND_HOME/config.yml`. Changes take effect on the next run. See the config file for full documentation.

## Required Permissions (for clean runs)

Any interactive session or scheduled task running this skill must have these permission patterns approved in `.claude/settings.local.json` to avoid per-call prompts (include both relative and absolute forms):

- `Bash(python3 brand-new-day/bnd-scan.py:*)` — JSearch API call
- `Bash(python3 brand-new-day/bnd-hash.py:*)` — dedup ID generation
- `Bash(python3 brand-new-day/bnd-render-dashboard.py)` — dashboard regeneration (no args)

Scheduled tasks with blanket `Bash` approval don't need these patterns. Manual runs from an interactive Claude Code session always do.

**Hard rule — NEVER use inline Python (`python3 -c "..."`, `python3 << 'PYEOF' ... PYEOF`) for scan-flow work.** Inline code with braces, quotes, or newlines can't be pattern-permitted and will prompt every invocation. Instead:

- JSON file reads/writes/edits → use Claude's native Read / Write / Edit tools. Don't shell out.
- Dedup ID generation → `python3 brand-new-day/bnd-hash.py <company> <title> <location>`
- Dashboard regeneration → `python3 brand-new-day/bnd-render-dashboard.py`
- JSearch API → `python3 brand-new-day/bnd-scan.py --query ... --date-posted ...`
- Never pipe any of the scan scripts into `jq`, `head`, `grep`, or another python invocation. They return parsed JSON on stdout — read the output directly and process in-memory.

Key tunables:
- `keywords.titles` — job title search terms
- `keywords.locations` — location filters
- `keywords.exclude_titles` — title exclusion patterns
- `sources` — job boards and ATS platforms to search
- `scoring.dimensions` — per-dimension weight and score_5/3/1 definitions (authoritative rubric)
- `scoring.weights` — legacy flat weights map, read at scoring time
- `scoring.hard_gates` — named-filter list of hard gates (e.g. location_fit)
- `scoring.comp_bands` — thresholds used by the comp_signals dimension
- `scoring.threshold` — minimum composite score to surface on dashboard
- `scheduling.operations_budget` — max tool calls per run
- `profile_path` — path to the user profile markdown (default: `{BND_HOME}/profile.md`)

## Data Layer

All persistent data: `$BND_HOME/data/`

| File | Purpose |
|---|---|
| `listings.json` | Every listing ever found — append-only audit log |
| `reviewed.json` | Review state per listing (new/reviewed/applied/passed) |
| `scan-state.json` | Run progress, batch tracking, pending queries |
| `run-log.json` | Run history with operation counts and error logs |
| `credit-ledger.json` | Credit usage tracking across all scanner-related activity |
| `issues.json` | Persistent issue/pattern log — survives across runs, tracks source health and systemic problems |

## Search Behavior (v1.5 — JSearch API)

1. Build queries: one JSearch API call per title keyword (4 queries per run)
2. Parse structured JSON responses — full JD text, salary, apply links included
3. Filter out excluded titles and already-seen listings (dedup)
4. Score directly from API data — no separate fetch step needed for most listings
5. For listings with missing JD text, enrich via WebFetch or Playwright

### How JSearch Works

JSearch (via RapidAPI) queries the Google Jobs index and returns structured JSON of **live postings only**. This replaced the v1.3 WebSearch + `site:` approach, which returned 80-100% stale URLs.

**API call format:**
```bash
python3 brand-new-day/bnd-scan.py --query "Product Manager remote" --date-posted week
```

The script handles URL encoding, key loading from `.env`, and JSON parsing. Output is the full JSearch response as pretty-printed JSON on stdout. Do NOT pipe — see "Required Permissions" section above.

**Key response fields per result:**
| Field | Maps to |
|---|---|
| `job_title` | title |
| `employer_name` | company |
| `job_location` | location |
| `job_description` | description (full JD text — usually 3K-8K chars) |
| `job_apply_link` | apply_url |
| `apply_options[]` | alternative apply links (prefer direct) |
| `job_min_salary` / `job_max_salary` | comp_range |
| `job_posted_at_datetime_utc` | posting_date |
| `job_is_remote` | remote signal (unreliable — verify from location/title/JD text) |
| `job_employment_type` | employment type |
| `job_highlights.Qualifications` | pre-parsed quals (useful for scoring) |
| `job_highlights.Responsibilities` | pre-parsed responsibilities |

**API budget:** 200 requests/month hard limit (free tier). At 4 queries/day = ~120 req/month. Track usage in `data/api-usage.json`.

**Known quirks:**
- `date_posted=today` returns HTTP 500 — use `week` or `3days`
- `job_is_remote` is often null even for remote roles — always check location string and JD text
- `remote_jobs_only=true` filter is unreliable — search broadly and filter ourselves
- Each `num_pages=1` call returns up to 10 results and costs 1 API request

### Deduplication

Listings dedup by normalized key: `hash(lowercase(company) + lowercase(title) + lowercase(location))`. Cross-platform duplicates get one entry; the apply URL prefers ATS board URLs over aggregator URLs.

## Scoring Rubric

**The rubric is data, not prose.** Load it from `$BND_HOME/config.yml` at scan time:

- `scoring.dimensions` — list of dimensions. Each has `name`, `weight`, `evaluate` (what to look for), and `score_5` / `score_3` / `score_1` descriptions. One entry has `hard_gate: true` instead of a weight.
- `scoring.hard_gates` — list of named hard gates (e.g. `location_fit`). Each has `pass_keywords` and `fail_action`.
- `scoring.comp_bands` — `high_usd` / `mid_usd` thresholds referenced by the `comp_signals` dimension.
- `scoring.weights` — flat weight map (currently the live source read at runtime; kept in sync with `dimensions[*].weight`).
- `scoring.threshold` — minimum composite to surface above the fold.

### How to score

Load the user profile from the path in `profile_path` (config.yml). Default: `{BND_HOME}/profile.md`. Then for each listing:

1. **Apply hard gates first.** For each entry in `scoring.hard_gates`, check the listing against `pass_keywords`. On fail, apply `fail_action` (currently only `score_zero` — composite forced to 0, listing still stored for audit).
2. **Score each weighted dimension 1–5** using the `score_5` / `score_3` / `score_1` anchors from config. Be calibrated, not generous. When in doubt, score 3 (neutral), not 4.
3. **For `comp_signals`** specifically: compare the listing's comp against `scoring.comp_bands` — at/above `high_usd` = 5, between `mid_usd` and `high_usd` (or unknown) = 3, below `mid_usd` = 1.
4. **Write a 1–2 sentence `fit_summary`** — direct and specific (e.g. "Growth PM role at a scaling analytics platform, core overlap on onboarding and PLG"), not marketing prose.

### Composite Calculation

```
weighted_sum = Σ(dimension_score × weight)   # skip hard-gate-only dimensions
max_possible = 5 × Σ(weights)
composite    = (weighted_sum / max_possible) × 5    # normalized 0-5
```

### Score Output

For each listing, produce:
- `composite_score` (0-5, one decimal)
- Per-dimension scores with a short note explaining the rating
- `fit_summary` — 1-2 sentence plain-language assessment

### Scoring Guidelines

- A 4.0+ should mean the user would genuinely want to apply. Calibrate accordingly.
- Rubric and weights live in config.yml — check them before scoring, the user may have tuned them.
- Never override the hard gate. Location fail → composite 0, period.

## Dashboard

Output: `$BND_HOME/dashboard.html`
Design baseline: `$BND_HOME/dashboard-v1.3.html` (frozen snapshot — never modify)

**Design rules (v1.4, signed off 2026-04-15):**
- Atlassian-inspired colors (#0052cc blue, #172b4d text, #fafbfc bg)
- System font stack (-apple-system, BlinkMacSystemFont, etc.) — NOT DM Sans
- LIGHT MODE ONLY — no dark backgrounds anywhere
- Full width — NO max-width constraint
- Score dimension grid with colored background boxes (green #e3fcef / yellow #fffae6 / red #ffebe6)
- Large composite score (28px) in card header, right-aligned

**Architecture:** Single self-contained HTML file. All listing data embedded as a JS array (`const LISTINGS = [...]`). Cards rendered dynamically at runtime. No external fetch() calls. Works via file:// protocol.

### Sections
1. **Header** — title, last run timestamp + source, new listing count, pending review count, run status badge
2. **State filter tabs** — New (default), Applied, Reviewed, Passed, All — with counts
3. **Above-threshold listing cards** — sorted by score desc, full card: title, company, composite score, location, source, posted date, fit summary, salary badge, score dimension grid, action buttons
4. **Card actions** — [Apply →], [Mark Applied] (blue outline), [Mark Reviewed], [Pass], card ID
5. **Below-threshold section** (collapsed) — condensed cards: title, company, score, summary, [View →], [Pass]
6. **Run log footer** — queries executed, sources, listings scored, notes/errors

### localStorage
Dashboard reads from BOTH `bnd-actions` and `bnd-v2-state` localStorage keys and merges (most advanced status wins). Writes to BOTH on every status change. Format for `bnd-actions`: `{ id: { status, timestamp } }`. Format for `bnd-v2-state`: `{ id: "status" }`.

### Source Health Panel

A persistent section rendered from `data/issues.json`. Does NOT get regenerated from scratch — the cron reads the existing issues file, appends/updates entries, and renders them into this section. Shows:
- Source-by-source health (working / degraded / broken)
- Open issues with severity and first-seen date
- Suggested direction for each issue (surfaced for user awareness, not auto-actioned)

This section persists across dashboard regenerations because it's data-driven from `issues.json`, not computed fresh each run.

### Review Tracking

Review state stored in `reviewed.json`. Dashboard uses localStorage for in-page actions; the next scanner run syncs localStorage → reviewed.json.

States: `new` → `reviewed` | `applied` | `passed`. All state changes are reversible. Passed listings are always accessible via the Passed tab.

## Interview-Prep Handoff

When the user says `prep me for listing [id]` or `/brand-new-day prep [company]`:
1. Resolve the listing from `listings.json`
2. Pass company name, role title, JD URL, and JD text to the interview-prep skill
3. Interview-prep generates the one-sheet as usual

The user never types a company name or URL that the system already has.

## Credit-Aware Execution

- Operations budget caps WebSearch + WebFetch calls per run (default: 50)
- If budget is hit mid-run, save remaining queries to `scan-state.json` as pending
- Next run executes pending queries first (catch-up), then new queries
- Priority: catch-up → ATS boards (Greenhouse, Lever, Ashby) → broad boards (Indeed, Built In, Wellfound)
- Target: every source searched at least every 48 hours even with batching

## Session-Start Protocol

**Every time** a Brand New Day command is invoked (any sub-command), do this FIRST before executing anything:

1. Read `data/run-log.json` — get the latest run entry (status, errors, operations used)
2. Read `data/issues.json` — get all open issues
3. Read `data/scan-state.json` — check for pending queries/fetches
4. Surface a brief summary to the user:
   - Last run: when, status (complete/partial), how many new listings
   - Open issues: count by severity, any new since last session
   - Pending work: any catch-up queries or fetches queued
5. **Do not auto-fix issues or start burning credits.** Present the summary and let the user decide what to focus on.

This ensures every session starts with awareness of what the cron produced overnight, without the user having to ask.

## Planning Protocol

When building or modifying Brand New Day (not just running scans), follow these rules before proposing any plan.

### PRD Citation Requirement

Every item in a plan must cite the PRD section it implements (e.g., "per §6.5.2, line 558"). If you cannot cite a specific PRD section, the item has not been verified against the source of truth.

- **PRD:** `~/Claude/Jobs/PRDs/versions/brand-new-day-prd-v1.5.md`
- **Reading guide:** `~/Claude/Jobs/PRDs/versions/prd-v1.5-reading-guide.md` (maps sections to line ranges for chunked reads)

Read the PRD yourself with the Read tool. Never plan from an agent summary or from memory alone.

### Scope Fence

Every plan must include a **"NOT in scope"** section that explicitly names:
- Items the user mentioned but deferred ("thinking out loud", "that is later")
- Phase 2+ features from PRD §10
- Anything not explicitly approved for the current session

If the user shares future thinking, acknowledge it and save to project memory as future context. Do not add it to the current plan.

### Memory-First Rule

Project memory (`project_brand_new_day.md`) gets updated as the **first deliverable** of any build session, before any code or config changes. If tracking is stale at session start, fix it before planning. This prevents the drift where plans diverge from actual project state.

---

## Execution Procedure — Full Scan (`/brand-new-day`)

Follow these steps exactly. Do not skip steps. Report progress to the user at natural milestones (after search phase, after scoring, after dashboard generation).

### Step 0: Load State

1. Read `$BND_HOME/config.yml` — load all settings (substitute `{BND_HOME}` placeholders)
2. Read `$BND_HOME/data/scan-state.json` — check for pending queries
3. Read `$BND_HOME/data/listings.json` — load existing listings for dedup
4. Read `$BND_HOME/data/reviewed.json` — load review states
5. Read the user profile from the path in `config.yml → profile_path` (default `{BND_HOME}/profile.md`)
6. Initialize an operations counter at 0 and set budget from `scheduling.operations_budget`
7. Initialize a run log entry: `{ run_id, trigger, started_at, status: "running", errors: [] }`

### Step 1: Build Query List

Construct JSearch queries by appending "remote" to the query text. The `remote_jobs_only` API param is broken (confirmed 2026-04-15) and without "remote" in the query, results are geo-biased to East Coast on-site roles.

**Query construction:**
```
query: "{title keyword} remote"
params: num_pages=1, date_posted=week
```

Use the top 2 title keywords for remote queries (broadest coverage):
1. `"Product Manager remote"` — catches Senior PM, Growth PM, Staff PM, etc.
2. `"Director of Product remote"` — catches Director, Sr. Director, Head of Product, etc.

Optionally add 2 more queries for local or specialized titles if budget allows:
3. `"Product Manager {location}"` — local/hybrid roles (use `keywords.locations[0]`)
4. `"Group Product Manager remote"` — if budget allows

Default: **4 queries per run** (well within the 200 req/month budget).

**Query ordering:**
1. **Catch-up queries** from `scan-state.json → pending_queries` (if any)
2. Remote queries first (highest signal)
3. Location-specific queries second

### Step 2: Search Phase (JSearch API)

> ⛔ **HARD RULE — no inline Python from here to end of scan.** Every step below (parse, dedup, quick-reject, build record, append) uses native Read / Write / Edit on small in-memory payloads. No `python3 -c`, no `python3 << 'PYEOF'`, no `jq`, no piping scan-script output. Each inline heredoc = a permission prompt that can't be "always allow"ed. See line 47. If you catch yourself typing `<< 'PYEOF'`, stop and use the native tool instead.

**Before starting:** Read `data/api-usage.json` to check monthly request count. If at or near 200, warn the user and stop.

For each query:

1. **Budget check:** If `operations_counter >= operations_budget` OR monthly API requests >= 200, stop. Save remaining queries to `scan-state.json → pending_queries`. Jump to Step 4.

2. **Execute JSearch API call** via the scan script, redirecting stdout to a per-query file:
   ```bash
   python3 brand-new-day/bnd-scan.py --query "{title keyword} remote" --date-posted week > /tmp/bnd-q{N}.json
   ```
   The script handles URL encoding, key loading, and JSON parsing. Redirect to a file — do NOT pipe into any other command (see "Required Permissions" section). Increment operations counter AND monthly API counter.

3. **Parse JSON response** with the native Read tool on `/tmp/bnd-q{N}.json`. Check `status` field — if not "OK", log error and continue to next query. Do NOT use inline python to parse.

4. **Process results:** For each item in `data[]` (in-context, no shell-outs):
   a. **Exclude check:** Does `job_title` contain any `exclude_titles` keyword (case-insensitive)? If yes, skip.
   b. **Dedup check:** Generate dedup key from `lowercase(employer_name)|lowercase(job_title)|lowercase(job_location)` with whitespace trimmed. If key exists in `listings.json`, skip.
   c. **Quick-reject:** Skip if title is clearly wrong role (e.g. "Project Manager" not "Product Manager"), or if `job_description` mentions hard domain locks (active clearance required, medical license, etc.)
   d. If new, add to the **score queue** with all structured data from the API response.

After all queries execute (or budget hit), report: "Search complete: X queries run, Y new listings found, Z skipped (duplicates/excluded/rejected)."

### Step 3: Score Phase

JSearch returns full JD text in most responses, so there's no separate fetch step. Score directly from the API data.

For each listing in the score queue:

1. **Check JD completeness:** If `job_description` is null or under 200 chars, mark `partial_data: true`. Optionally try WebFetch on the `job_apply_link` to get the full JD — but only if operations budget allows. If fetch fails, score from available data.

2. **Extract listing data** from the API response:
   ```
   title:        job_title (clean, no company prefix)
   company:      employer_name
   location:     job_location (+ check job_city, job_state, job_is_remote)
   description:  job_description (full JD text)
   apply_url:    job_apply_link (prefer is_direct=true from apply_options[])
   comp_range:   "{job_min_salary}-{job_max_salary} {job_salary_period}" or null
   posting_date: job_posted_at_datetime_utc
   partial_data: true if job_description is null/short, false otherwise
   ```

3. **Generate dedup ID:** Run `python3 brand-new-day/bnd-hash.py "<company>" "<title>" "<location>"`. The script returns the 8-char hex hash on stdout. If this exact ID already exists in `listings.json`, skip.

4. **Score the listing** against the rubric loaded from `config.yml` (see Scoring Rubric section above):
   - Apply each entry in `scoring.hard_gates` first. Any fail → composite = 0, still store.
   - Score all weighted dimensions in `scoring.dimensions` independently (1-5 each) with a short note per dimension.
   - For `comp_signals`, reference `scoring.comp_bands`.
   - Compute weighted composite score normalized to 0-5 scale.
   - Write a 1-2 sentence `fit_summary`.

5. **Build the listing record:**
   ```json
   {
     "id": "<8-char-hash>",
     "title": "...",
     "company": "...",
     "location": "...",
     "url": "...",
     "apply_url": "...",
     "source": "JSearch",
     "description": "<full JD text>",
     "posting_date": "...",
     "discovered_at": "<ISO 8601 timestamp>",
     "comp_range": "...",
     "partial_data": false,
     "scores": {
       "composite": 4.2,
       "dimensions": {
         "location_fit": { "score": 5, "gate": "pass", "note": "Remote" },
         "seniority_fit": { "score": 5, "note": "Senior PM" },
         "domain_match": { "score": 4, "note": "..." },
         "growth_plg": { "score": 5, "note": "..." },
         "platform_architecture": { "score": 4, "note": "..." },
         "company_stage": { "score": 4, "note": "..." },
         "role_clarity": { "score": 4, "note": "..." },
         "people_management": { "score": 3, "note": "..." },
         "comp_signals": { "score": 3, "note": "..." },
         "application_friction": { "score": 5, "note": "..." }
       },
       "fit_summary": "..."
     }
   }
   ```

6. **Append the listing to `listings.json`** using native Read + Write (not inline python):
   - Read `$BND_HOME/data/listings.json` → parse JSON array
   - Append the new listing record(s) to the array
   - Write the full updated array back to `listings.json` (pretty-printed, 2-space indent)

7. **Add review entry to `reviewed.json`** using the same Read → modify → Write pattern:
   ```json
   { "<id>": { "status": "new", "first_seen": "<date>", "reviewed_at": null, "applied_at": null, "notes": null } }
   ```

After all scoring (or budget hit), report: "Scored X listings. Y above threshold, Z below threshold, W failed location gate."

### Step 4: Sync Review Actions

Before generating the dashboard, check if `$BND_HOME/data/review-actions.json` exists (written by dashboard localStorage JS). If it does, use native Read / Write / Bash(rm) — not inline python:
1. Read `review-actions.json`
2. Read `reviewed.json`, merge each action into the corresponding entry (update status + timestamp), Write `reviewed.json` back
3. Delete `review-actions.json` via `rm` after syncing

### Step 5: Generate Dashboard

Run:
```bash
python3 brand-new-day/bnd-render-dashboard.py
```

The render script reads `data/listings.json` + `data/run-log.json`, regenerates `dashboard.html` in place, and prints a one-line summary (`Dashboard updated: N listings (M above threshold).`). All CSS, HTML structure, and JS logic are preserved — only the embedded `LISTINGS` array and `RUN_LOG` object are replaced.

**Design reference:** `dashboard-v1.3.html` (frozen, never modify). The render script targets the v1.4+ data shape.

**Dimension mapping** (handled by the script — documented here for reference):
- seniority_fit → "Seniority", domain_match → "Domain", growth_plg → "Growth/PLG"
- platform_architecture → "Platform", company_stage → "Stage", role_clarity → "Clarity"
- people_management → "People Mgmt", application_friction → "Friction"
- comp_signals and location_fit → not shown as dimensions (comp shown via salary badge, location via locationFail flag)

**Above threshold (≥3.5):** Full card with score grid (dims array populated).
**Below threshold (<3.5):** Condensed card (empty dims array).
**Location fail (gate=fail):** score=0, locationFail=true, goes to below-threshold.

If the script exits non-zero, read its stderr for the reason (typically a malformed dashboard template it couldn't locate `LISTINGS`/`RUN_LOG` in). Do not fall back to inline python — fix the template or the script.

### Step 6: Finalize Run

All JSON updates in this step use native Read → modify → Write (never inline python).

1. **Update `scan-state.json`:**
   ```json
   {
     "last_run": {
       "started_at": "...",
       "completed_at": "...",
       "status": "complete",
       "operations_used": N,
       "operations_budget": 50
     },
     "pending_queries": [],
     "pending_fetches": [],
     "sources_last_searched": { "jsearch": "2026-04-15", ... }
   }
   ```

2. **Append to `run-log.json`:**
   ```json
   {
     "run_id": "<date>-<seq>",
     "trigger": "manual",
     "started_at": "...",
     "completed_at": "...",
     "status": "complete",
     "queries_executed": N,
     "queries_pending": N,
     "listings_found": N,
     "listings_new": N,
     "listings_duplicate": N,
     "listings_above_threshold": N,
     "operations_used": N,
     "errors": []
   }
   ```

3. **Update `issues.json`:**
   - Read existing issues
   - For each error from this run, check if a matching issue already exists (by `id` pattern)
     - If yes: increment `occurrences`, update `last_seen`
     - If no: append a new issue with `status: "open"`, `first_seen: today`, `occurrences: 1`
   - Never delete or resolve issues automatically — only the user resolves issues
   - Issue IDs should be kebab-case descriptive slugs (e.g., `builtin-all-404`, `stale-urls-websearch`)

4. **Report to the user** with a brief summary: new listings count, top-scoring listings (title + company + score), any errors or pending items, and remind them to open the dashboard.

---

## Execution Procedure — Sub-Commands

### Validation Procedure (shared by `init` and `doctor`)

The validator runs five checks. `init` runs them on a fresh install (and writes starter files if any are missing); `doctor` runs them against an existing install (read-only, never overwrites).

1. **Config parses.** Read `$BND_HOME/config.yml`. Confirm it parses as YAML and has the expected top-level keys (`keywords`, `sources`, `scoring`, `scheduling`, `output`, `profile_path`).
2. **BND_HOME is writable.** Confirm `$BND_HOME` exists and is writable (try a touch + rm of a `.bnd-write-test` file).
3. **`.env` has `RAPIDAPI_KEY`.** Read `$BND_HOME/.env`. Confirm `RAPIDAPI_KEY=` is present and non-placeholder (i.e. not `your_rapidapi_key_here`).
4. **JSearch test call works.** Run `python3 $BND_HOME/bnd-scan.py --query "Product Manager remote" --date-posted week` with a small `--num-pages 1`. Confirm valid JSON output with `data` array. This costs 1 API request — note it in the user-facing summary.
5. **Profile loads.** Read the file at `profile_path` (resolved via `{BND_HOME}` substitution). Confirm it's non-empty and not the literal `.example` template content.

Report each check's result as a one-line ✓ or ✗ with a short explanation. After the five checks, print a summary: "5/5 passed" or "N issue(s) — see above."

### `/brand-new-day init`

For first-time setup after `install.sh`. Validates the install and creates starter data files if missing.

1. Run the **Validation Procedure** above. Report results.
2. For each missing file in `$BND_HOME/data/`, write a minimal starter:
   - `listings.json` → `[]`
   - `reviewed.json` → `{}`
   - `scan-state.json` → `{}`
   - `run-log.json` → `[]`
   - `api-usage.json` → `{}`
   - `credit-ledger.json` → `{}`
   (Note: `install.sh` already creates these. This step is a safety net for users who installed manually or wiped `data/`.)
3. If validation passed all 5 checks, print: "Ready. Run `/brand-new-day` to start your first scan."
4. If any validation check failed, print the failures and how to fix each. Do NOT proceed to first scan.

### `/brand-new-day doctor`

For diagnosing an existing install when something seems off.

1. Run the **Validation Procedure**. Report results.
2. Additionally, sanity-check the data layer:
   - `data/listings.json` parses as JSON array
   - `data/reviewed.json` parses as JSON object
   - `data/run-log.json` parses as JSON array; report the most recent entry's `status` and `completed_at`
   - `data/api-usage.json` parses; report current month's request count
3. Print a summary. Read-only — never overwrites or repairs files. The user decides whether to run `init`, `reset`, or fix manually.

### `/brand-new-day reset`

For users who want to wipe their pipeline and start fresh — keeps the install, archives the data.

1. **Confirm with the user before doing anything.** Show what will happen: "This will move `$BND_HOME/data/*.json` to `$BND_HOME/data/archive-{YYYY-MM-DD}/` and create empty starters. Your config, profile, and `.env` are not affected. Continue?"
2. If the user says no, stop.
3. If yes:
   a. `mkdir -p $BND_HOME/data/archive-{YYYY-MM-DD}` (use today's date in ISO format)
   b. Move every `*.json` file in `$BND_HOME/data/` (not subdirectories) into the archive dir
   c. Re-create empty starters (same set as `init` step 2)
   d. If `dashboard.html` exists, replace it with a copy of `$BND_HOME/dashboard-template.html` if available, otherwise leave it
4. Report: "Reset complete. {N} files archived to data/archive-{date}/. Empty starters created. Run `/brand-new-day` to begin a fresh pipeline."

### `/brand-new-day status`

1. Read `scan-state.json` and `run-log.json`
2. Display: last run time, status (complete/partial), operations used, pending queries if any
3. Read `reviewed.json` — count by status (new/reviewed/applied/passed)
4. Report in a compact summary

### `/brand-new-day review`

1. Read `listings.json` and `reviewed.json`
2. Show unreviewed listings one at a time (title, company, score, fit summary)
3. The user says "reviewed", "apply", "pass", or "skip"
4. Update `reviewed.json` with the new status + timestamp
5. Continue until all unreviewed are processed or the user says "done"

### `/brand-new-day rescore`

1. Read `$BND_HOME/config.yml` for current weights/thresholds
2. Read the user profile from `profile_path`
3. Read `listings.json` — filter to unreviewed listings
4. Re-score each listing using the current rubric and weights
5. Update scores in `listings.json`
6. Regenerate `dashboard.html`
7. Report: how many rescored, any significant score changes

### `/brand-new-day prep [id or company]`

1. Read `listings.json`
2. Resolve the reference — match by listing ID or company name (fuzzy match OK)
3. If ambiguous, show matches and ask the user to pick
4. Load the listing: company, title, URL, full JD text
5. Invoke the interview-prep skill with this data pre-loaded
6. The user never types a company name or URL — it flows from the data layer

---

## Quality Standards

- No AI slop in fit summaries. Write like a sharp colleague, not a marketing brochure.
- Be honest about weak matches. A 2.5 is a 2.5.
- Never surface a listing that fails the location hard gate, regardless of other scores.
- Always degrade gracefully: if a source is blocked, skip it and note it. Never fail silently.
