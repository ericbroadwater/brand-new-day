# Brand New Day — Product Requirements Document

| | |
|---|---|
| **Version** | `1.5` |
| **Author** | `Eric Broadwater + Claude` |
| **Date** | `2026-04-16` |
| **Status** | `Signed Off — 2026-04-16 (patched 2026-04-22, 2026-04-27). Phase 1.5 COMPLETE 2026-04-27.` |
| **Supersedes** | `v1.4 (signed 2026-04-15) — Phase 1 complete` |
| **Patches** | `2026-04-22 P1 — Added §8.2.0 (replication-ready scan invocation); 2026-04-22 P2 — Extended §8.2.0 (helpers + native tools for full scan flow); 2026-04-27 P3 — Phase 1.5c shipped + pre-commit hook hardening; 2026-04-27 P4 — Phase 1.5d shipped (install.sh + init/doctor/reset subcommands), Phase 1.5 complete` |
| **Version History** | `Versioned in source repository. Prior versions retained as v1.1, v1.2, etc.` |

---

> **Publication notes:** This PRD was originally written as an internal design document during BND development (drafted 2026-04-16, patched through 2026-04-27). It was published to this repository on 2026-04-29 as a historical artifact alongside the v0.1.0 alpha release. Personal filesystem paths, references to unrelated private projects, and job-search operational details have been redacted; all design decisions and scope are preserved as written. Author attribution is retained on the title page and in Appendix B.

---

## 1. Executive Summary

Brand New Day is a Claude Code skill that automates the daily grind of finding, evaluating, and surfacing relevant Product Manager job listings. It searches public job boards and ATS platforms by job title keywords, scores each listing against the user's profile, and outputs a local HTML dashboard of high-scoring matches each morning.

It replaces the current 1-2 hour daily manual workflow of opening email digests, clicking through listings, and copy-pasting JDs into Claude for evaluation. It does NOT auto-apply. It finds, scores, and surfaces — the user decides what to pursue.

The skill sits upstream of an external one-sheet generator. Once the user picks a listing worth pursuing, they can generate a tailored one-sheet with one command.

**Phase 1 status: ✅ COMPLETE (shipped in Phase 1).** v1.5 adds Phase 1.5 — GitHub alpha packaging — which turns the working single-user pipeline into a public, replicable repo another technically-capable user could install and run against their own profile.

---

## 2. Problem Statement

The user is a senior product manager in active job search. Their current daily process:

1. Open email digests from 6 platforms (LinkedIn, Indeed, Built In, Wellfound, PM Job Board, Google Alerts)
2. Click through each listing link individually
3. Read the JD, mentally evaluate fit
4. Copy promising JDs into Claude chat to get a scored assessment
5. Decide whether to apply

This costs 1-2 hours daily of repetitive, low-leverage work. On a real day, that looks like: open email, click link, skim JD, open Claude, paste JD, wait for assessment, repeat 15-20 times. The evaluation criteria are consistent — the same dimensions get checked every time. The bottleneck isn't judgment, it's the manual collection and triage.

Meanwhile, rejections arrive and the pipeline needs constant feeding. Every hour spent on triage is an hour not spent on tailoring applications for the roles that actually matter.

### What stays manual (for now)

- **LinkedIn email digests** — LinkedIn's anti-bot enforcement and TOS make automation risky. Many PM roles only post there. The user continues checking these manually.
- **Google Alerts** — Currently delivers via email. Manual review continues.
- **Application submission** — Always manual. The user tailors each application.

The system should remember that automating LinkedIn and Google Alerts are future goals.

---

## 3. Goals & Success Metrics

### Primary Goals

| Goal | Metric | Target |
|---|---|---|
| Reduce daily search time | Minutes spent on manual job triage | < 15 min (down from 60-120) |
| Surface relevant listings faster | Time from posting to the user seeing it | < 48 hours |
| Improve signal-to-noise ratio | % of surfaced listings the user acts on | > 50% of scored 4.0+ |
| Zero missed strong matches | Listings the user finds manually that scanner missed | < 1/week |

### Secondary Goals

- Build a searchable historical record of all evaluated listings
- Create a data-driven feedback loop to tune scoring over time
- Integrate cleanly with an external one-sheet generator

---

## 4. User Stories

| # | As a User, I want to... | So that... |
|---|---|---|
| 1 | Open a single dashboard each morning showing new high-fit listings | I skip the 6-platform email grind |
| 2 | See a score breakdown for each listing | I understand why the system thinks it's a fit (or not) |
| 3 | Click directly to the job posting to apply | There's zero friction between "this looks good" and "I'm applying" |
| 4 | Generate an interview prep one-sheet from the dashboard | The workflow from discovery to prep is seamless |
| 5 | Mark listings as reviewed so they don't resurface | My dashboard stays clean without losing history |
| 6 | Adjust scoring weights and thresholds without editing code | I can tune the system as I learn what works |
| 7 | Add or remove search keywords easily | My search adapts as I refine my target roles |
| 8 | Trust that the scanner runs overnight without burning daytime credits | My interactive Claude sessions aren't affected |
| 9 | Know if a run didn't complete and what's pending | I'm never wondering if the system is working |
| 10 | See the same listing only once, even if it appears on multiple boards | Dedup is handled, not my problem |

---

## 5. Design Principles

1. **No copy-paste. Ever.** If a workflow step requires the user to copy a command from one place and paste it into another, it's not automated — it's just relocated manual work. Every action must be executable without copy-paste.

2. **Overnight credits, morning results.** The scanner runs in the overnight window (10pm-6am) when credits would otherwise go unused. The user's daytime work blocks must be protected. Credits must be fresh by morning.

3. **Degrade gracefully.** If a source is blocked, skip it and note it. If credits run out mid-run, save state and resume tomorrow. Never fail silently — always surface what happened and what's pending.

4. **Audit everything, display only what's new.** Every listing ever found is stored permanently. But the dashboard only shows what the user hasn't reviewed yet. History is always available, never in the way.

5. **Automate what's automatable. Flag what isn't (yet).** LinkedIn and Google Alerts stay manual today. The system explicitly tracks these as future automation targets rather than pretending they don't exist.

---

## 6. System Architecture

### Overview

```
┌─────────────────────────────────────────────────────┐
│                    SCHEDULER                         │
│   Cron (midnight) OR manual (/brand-new-day)           │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│                  SEARCH ENGINE                       │
│   JSearch API (primary) — title-first keyword search │
│   Adzuna API (supplemental) — different aggregation  │
│   → Returns structured JSON of live postings         │
│   → Dedup against seen listings                      │
│   → Budget-aware: stops when operation cap reached   │
└─────────────┬───────────────────────────────────────┘
              │ structured listing data
              ▼
┌─────────────────────────────────────────────────────┐
│                 JD ENRICHMENT                         │
│   Most data comes from API response directly         │
│   → Extract: title, company, location, description,  │
│     apply URL, comp (if visible), posting date        │
│   → WebFetch/Playwright for missing JD text          │
│   → Store raw JD text                                │
└─────────────┬───────────────────────────────────────┘
              │ structured listing data
              ▼
┌─────────────────────────────────────────────────────┐
│                SCORING ENGINE                        │
│   Claude reads JD against the user's profile             │
│   → Score each dimension (configurable weights)      │
│   → Apply hard gates (location)                      │
│   → Compute weighted composite score                 │
│   → Generate 1-line fit summary                      │
└─────────────┬───────────────────────────────────────┘
              │ scored listings
              ▼
┌─────────────────────────────────────────────────────┐
│                  DATA LAYER                           │
│   listings.json — all listings ever seen (audit)     │
│   scan-state.json — run progress, batch tracking     │
│   reviewed.json — which listings the user has reviewed    │
└─────────────┬───────────────────────────────────────┘
              │ new unreviewed listings above threshold
              ▼
┌─────────────────────────────────────────────────────┐
│                  DASHBOARD                           │
│   Local HTML file (card-based, light mode)           │
│   → Listings scored above threshold                  │
│   → Score breakdowns, apply links, one-sheet links   │
│   → Run metadata (when it ran, what's pending)       │
└─────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Claude IS the scoring engine.** No separate ML model or API. Claude reads the JD text and scores it. This is the same thing the user does today when he pastes a JD into chat — we're just automating the collection step.

2. **Keyword-based search, not company-based.** The original brief proposed scraping specific company career pages. The user doesn't have a fixed target company list, and good PM roles appear at companies he hasn't heard of. Keyword search via job aggregator APIs casts a wider net. (v1.3 used WebSearch + `site:` operators; v1.4 replaced this with JSearch/Adzuna APIs after the `site:` approach proved unviable — see Appendix D.)

3. **Budget-aware execution.** Claude Pro has credit limits. The skill tracks operations performed and stops when it hits a configurable cap, saving state to resume next run.

4. **Dedup by content, not URL.** The same listing may appear on Indeed, the company's Greenhouse page, and Built In. Dedup uses a normalized key of (company + title + location) to catch cross-platform duplicates.

---

## 6. Detailed Requirements

### 6.1 Search Engine ✅ COMPLETE

#### 6.1.1 Search Keywords

The skill searches by job title. The keyword list is configurable in `config.yml`. Default keywords:

```yaml
keywords:
  titles:
    - "Product Manager"        # Inclusive — catches Senior PM, Growth PM, etc.
    - "Director of Product"
    - "Head of Product"
    - "Group Product Manager"
  locations:
    - "remote"
    - "San Diego"
```

**Inclusive matching:** A search for `"Product Manager"` should return results containing "Senior Product Manager", "Growth Product Manager", "Staff Product Manager", etc. The title filter is deliberately broad — the scoring engine handles precision.

**Exclusion keywords** (applied during result filtering, not in the search query itself):

```yaml
exclude_titles:
  - "intern"
  - "associate"
  - "junior"
  - "engineer"
  - "designer"
  - "marketing manager"
  - "project manager"
  - "program manager"
```

#### 6.1.2 Discovery Sources

The skill discovers listings through job aggregator APIs that return structured JSON of live postings. This replaced the v1.3 WebSearch + `site:` approach, which returned 80-100% stale/expired URLs across 4 test runs (see Appendix D for details).

**Primary — JSearch (RapidAPI):**

| | |
|---|---|
| **Endpoint** | JSearch via RapidAPI |
| **Method** | Title-first keyword search with location filter |
| **Free tier** | 200 requests/month (hard limit), 1,000 requests/hour rate limit |
| **Data returned** | 30+ fields: title, company, location, full JD text, salary, apply link, posting date |
| **Coverage** | Aggregates from Google Jobs index (Indeed, LinkedIn, Glassdoor, ZipRecruiter, company career sites) |

**Why JSearch:** It queries the same Google Jobs index that the `site:` approach was trying to reach, but returns structured JSON of only live postings. Same data source, better interface, no stale URLs.

**Supplemental — Adzuna:**

| | |
|---|---|
| **Endpoint** | Adzuna API |
| **Free tier** | ~250 requests/day |
| **Data returned** | Title, company, description, salary, location, redirect URL, posting date |
| **Coverage** | Different aggregation source from JSearch. 12 countries. |

**Why Adzuna:** Different aggregation pipeline provides listings JSearch may miss. An Adzuna MCP server exists (`folathecoder/adzuna-job-search-mcp`) for potential direct integration.

**Direct ATS APIs (Phase 2 — targeted company monitoring):**

Documented endpoints for direct ATS queries. These require a curated company seed list but return only live postings:

| ATS | Endpoint | Notes |
|---|---|---|
| **Workday** | `myworkdayjobs.com/wday/cxs/{subdomain}/{companyId}/jobs` | POST, paginated. Has "Posted Today" filter. |
| **Lever** | `api.lever.co/v0/postings/{org}?mode=json` | GET. Plain fetch, no Playwright. |
| **Ashby** | `jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams` | POST (GraphQL). Structured data. |
| **Greenhouse** | `boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true` | GET. Already tested in v1.3. |

**Deferred to Phase 2** because the seed list approach is company-first, not title-first. JSearch handles broad title-first discovery; direct ATS APIs would add targeted monitoring for specific companies the user is watching.

**Deprecated — WebSearch + `site:` operators:**

The v1.3 approach used `site:indeed.com`, `site:boards.greenhouse.io`, etc. After 4 runs (2 manual, 2 scheduled), this approach yielded:
- 80-100% stale/expired URLs across all sources
- 0 new listings on the final run (Apr 10)
- Root cause: Google caches old ATS job pages long after roles close

Retained as an optional fallback in `config.yml` but no longer the primary discovery path.

**What's NOT included and why:**
- **LinkedIn** — Anti-bot enforcement, TOS risk. Stays manual. (Future automation target.)
- **Google Alerts** — Email-based, no public search interface for alerts. Stays manual.
- **Indeed API** — Shut down. Remaining Sponsored Jobs API requires active ad spend.
- **ZipRecruiter API** — Deprecated March 2025. Returns nothing.
- **Wellfound / Built In** — No public APIs. Wellfound confirmed login-walled.

#### 6.1.3 Search Query Construction

Each run generates API queries by combining title keywords with location filters:

**JSearch queries:**
```
query: "Product Manager", location: "San Diego, CA", remote_jobs_only: false, date_posted: "today"
query: "Director of Product", location: "San Diego, CA", remote_jobs_only: false, date_posted: "today"
query: "Head of Product", location: "United States", remote_jobs_only: true, date_posted: "today"
... (repeat for each title keyword)
```

With 4 title keywords × ~2 location variants = **~8 JSearch queries per full run.** Each query returns up to 10 results (configurable). This is significantly more efficient than the v1.3 approach (24 queries) and stays well within the 1,000 req/mo free tier.

**Adzuna queries** follow a similar pattern with `what` (title) and `where` (location) params.

To stay within API rate limits, the skill tracks requests per month in `scan-state.json` (see §6.5 Credit Management).

#### 6.1.4 Result Processing

For each API response:
1. Parse structured JSON results (title, company, location, description, apply URL, posting date, comp range)
2. Filter out results matching `exclude_titles`
3. Filter out results already in `listings.json` (dedup check)
4. For listings with full JD text in the API response, proceed directly to scoring
5. For listings with partial/missing JD text, add to the enrichment queue (WebFetch or Playwright to get full JD)

#### 6.1.5 Adding Sources

New aggregator APIs can be added to `config.yml`:

```yaml
sources:
  - name: "JSearch"
    type: "aggregator_api"
    enabled: true
    priority: 1
  - name: "Adzuna"
    type: "aggregator_api"
    enabled: true
    priority: 2
  # Direct ATS APIs (Phase 2) would go here with type: "ats_api"
```

Because JSearch and Adzuna aggregate across many boards, adding a new source means adding a new API provider — not a new site: filter. The aggregators already cover Indeed, LinkedIn (public postings), Glassdoor, ZipRecruiter, and company career sites.

#### 6.1.6 Source Discovery (Future)

**Automated source discovery (Phase 2+):** Claude should track ATS platforms encountered during scoring. When a company uses an ATS with a known direct API (Workday, Lever, Ashby, Greenhouse), it gets logged as a candidate for direct monitoring — the user approves which companies to add to the seed list.

**Email digest parsing (Future):** LinkedIn, Google Alerts, and other email-based digests could be parsed by reading the email content and extracting listing URLs. This would convert manual email checking into automated ingestion. Method TBD — likely email forwarding to a parseable inbox or direct IMAP access. Tracked as a future automation target alongside LinkedIn and Google Alerts.

---

### 6.2 Scoring Engine ✅ COMPLETE

#### 6.2.1 How Scoring Works

Claude reads the full JD text and evaluates it against the user's profile (loaded from `references/resume.md`). Each dimension is scored 1-5 independently, then a weighted composite is calculated.

This is the same evaluation the user currently does by pasting JDs into Claude chat. The scoring dimensions formalize what Claude already assesses intuitively.

#### 6.2.2 Scoring Dimensions

| # | Dimension | What it measures | Weight | Type |
|---|---|---|---|---|
| 1 | **Location Fit** | Remote, San Diego, or hybrid SD = pass. On-site elsewhere = fail. | — | **Hard Gate** |
| 2 | **Seniority Fit** | Senior/Director/Group/Head PM = 5. Mid-level PM = 3. Junior/Associate = 1. | 2.0x | Weighted |
| 3 | **Domain Match** | SaaS, CMS, DXP, platforms, publishing, content = 5. Adjacent (martech, analytics) = 4. Neutral (e-commerce, fintech) = 3. Hard domain lock ("must have FHIR/healthcare/defense clearance") = 1. | 2.0x | Weighted |
| 4 | **Growth/PLG Relevance** | Onboarding, activation, lifecycle, trials, PLG, experimentation, conversion = 5. General PM with no growth angle = 2. | 2.0x | Weighted |
| 5 | **Platform/Architecture** | API-first, headless, data infrastructure, developer tools, platform PM = 5. Standard B2B SaaS = 3. Consumer app = 2. | 1.0x | Weighted |
| 6 | **Company Stage** | Funded/growing company with real product and traction = 5. Pre-product startup = 3. Vague consulting shop / body shop = 1. | 1.0x | Weighted |
| 7 | **Role Clarity** | Clear JD with specific problems, real metrics, defined scope = 5. Buzzword soup, generic responsibilities = 2. | 1.0x | Weighted |
| 8 | **People Management** | Managing PMs or cross-functional teams = 5. IC with leadership scope = 3. Pure IC = 2. | 1.0x | Weighted |
| 9 | **Comp Signals** | $160K+ base (posted) = 5. $140-160K = 4. Below $140K = 2. Not posted = 3 (neutral). | 0.5x | Weighted |
| 10 | **Application Friction** | Direct apply or simple form = 5. Reasonable process = 3. "5 references, cover letter required, assessment test" = 1. | 0.5x | Weighted |

**Tunability note:** These scoring signals are the initial calibration based on the user's profile and priorities. Post-launch, this is the area most likely to need adjustment as we see how scores map to the user's actual interest in real listings. All weights are in `config.yml` and can be changed without code edits. Dimension definitions in `SKILL.md` can also be refined. The system should make it easy to answer: "Why did this listing score a 4 when I thought it was a 2?" — and then adjust.

#### 6.2.3 Composite Score Calculation

```
Weighted sum = Σ (dimension_score × weight)
Max possible = Σ (5 × weight)  →  5 × (2+2+2+1+1+1+1+0.5+0.5) = 5 × 11 = 55
Composite = (weighted_sum / max_possible) × 5  →  normalized to 0-5 scale
```

**Hard gate behavior:** If Location Fit fails, the listing gets a composite score of 0 regardless of other dimensions. It still gets stored in `listings.json` for audit purposes but is never surfaced on the dashboard.

#### 6.2.4 Score Output Per Listing

For each scored listing, the engine produces:

```json
{
  "composite_score": 4.2,
  "dimensions": {
    "location_fit": { "score": 5, "note": "Remote" },
    "seniority_fit": { "score": 5, "note": "Senior PM" },
    "domain_match": { "score": 4, "note": "Analytics platform — adjacent to DXP" },
    "growth_plg": { "score": 5, "note": "Owns onboarding + activation" },
    "platform_architecture": { "score": 4, "note": "API-first, developer audience" },
    "company_stage": { "score": 4, "note": "Series C, $50M ARR" },
    "role_clarity": { "score": 4, "note": "Clear scope, specific metrics mentioned" },
    "people_management": { "score": 3, "note": "IC role, cross-functional leadership" },
    "comp_signals": { "score": 3, "note": "Not posted" },
    "application_friction": { "score": 5, "note": "Apply on Greenhouse, no extras" }
  },
  "fit_summary": "Strong growth PM role at a scaling analytics platform. Core overlap on onboarding, PLG, and data layer work. IC but with clear cross-functional scope."
}
```

#### 6.2.5 Configurable Scoring

All weights, hard gates, and thresholds are defined in `config.yml` and can be changed without editing skill code:

```yaml
scoring:
  hard_gates:
    location_fit:
      pass_values: ["remote", "san diego", "hybrid"]
      fail_action: "score_zero"  # score 0, still store for audit

  weights:
    seniority_fit: 2.0
    domain_match: 2.0
    growth_plg: 2.0
    platform_architecture: 1.0
    company_stage: 1.0
    role_clarity: 1.0
    people_management: 1.0
    comp_signals: 0.5
    application_friction: 0.5

  threshold: 3.5  # Only surface listings at or above this score
```

To add a new hard gate (e.g., seniority), move it from `weights` to `hard_gates` in the config. To adjust what "good" means for any dimension, the scoring rubric in the SKILL.md is the reference.

---

### 6.3 Dashboard ✅ COMPLETE

#### 6.3.1 Output Format

A single self-contained HTML file generated at the end of each run:

**File:** `{BND_HOME}/dashboard.html`

The dashboard uses the same design system as the author's one-sheet artifacts: card-based layout, light mode, DM Sans + DM Mono, responsive, print-friendly.

#### 6.3.2 Dashboard Sections

**Header:**
- Title: "Brand New Day"
- Subtitle: last run timestamp, number of new listings, number pending review
- Status bar: if the last run was incomplete, show "X sources pending — will resume tonight"

**New Listings (main section):**

Each listing is a card. Card contents:

- Job title (h3)
- Company name
- Composite score (large, monospace, accent-colored)
- Location
- Posting date (if available)
- Fit summary (1-2 sentences from the scoring engine)
- Score breakdown (compact grid — each dimension's score + note; may need to combine dimensions if too dense in practice)
- Listing ID (short hash for reference in `/brand-new-day` commands)

Action buttons per card:

- `[Apply →]` — direct link to the job posting / application page (opens in browser)
- `[Prep One-Sheet]` — triggers external one-sheet generation (see §9.1 for mechanism)
- `[Mark Reviewed]` — in-page button that updates review state via minimal JS (see §7.3.3)
- `[Pass]` — marks listing as "passed" (see §7.3.3 for recovery)

Cards sorted by composite score, highest first.

**State filter tabs:**

The dashboard includes filter tabs at the top of the listings section to view listings by state:

- **New** (default view) — unreviewed listings from the latest run
- **Applied** — listings the user has marked as applied
- **Reviewed** — listings marked as reviewed but not applied
- **Passed** — listings marked as passed (accessible for recovery — see §7.3.3)
- **All** — everything regardless of state

This ensures the user can always find any listing regardless of its current state. No listing is ever hidden permanently.

**Below-threshold listings (collapsed section):**
A collapsible section showing listings that scored between 2.0 and the threshold. Helps the user see what's being filtered out and whether the threshold needs adjusting. Minimal display — title, company, score, fit summary only.

**Run Log (footer):**
- Sources searched this run
- Total new listings found
- Listings scored above threshold
- Listings filtered (location gate, duplicates, below threshold)
- Credit budget used (operations count)
- Errors or failed fetches, if any

#### 7.3.3 Review Tracking

**How it works:**

All listing state lives in `reviewed.json`:

```json
{
  "abc123": {
    "status": "new",           // new | reviewed | applied | passed
    "first_seen": "2026-04-06",
    "reviewed_at": null,
    "applied_at": null,
    "notes": null
  }
}
```

**Display logic:** The dashboard defaults to showing listings with `status: "new"`. Other states are accessible via filter tabs (see §6.3.2). No listing is ever hidden from the user — just organized by state.

**State overrides:** the user can change any listing's state at any time:

- Passed a listing by mistake? → Switch to the Passed tab, click `[Undo Pass]` to move it back to New
- Scanner scored something low but the user wants to apply? → Override from any state to Applied
- Applied to something the scanner flagged as a pass? → Override from Passed to Applied

Every state change is timestamped in `reviewed.json` for audit.

**How the user marks items reviewed — zero copy-paste:**

The dashboard includes minimal JavaScript (~30 lines) that handles review actions in-page:

1. **`[Mark Reviewed]` / `[Pass]` buttons** — clicking writes to `reviewed.json` via a tiny local Node.js server that starts with the dashboard (or alternatively, the buttons write to `localStorage` and the next skill run syncs `localStorage` → `reviewed.json`).
2. **Batch review** — a "Mark All Reviewed" button in the header clears the full dashboard in one click.
3. **`/brand-new-day review`** — still available as a CLI fallback. The skill loads unreviewed listings and the user marks "reviewed" or "pass" interactively. No copy-paste of IDs or commands.

**Preferred approach for v1:** localStorage-based. The dashboard JS stores review actions in the browser. On the next scanner run, the skill reads the dashboard's companion `review-actions.json` file (written by the dashboard's JS) and syncs it into `reviewed.json`. This avoids running a local server while still being zero-copy-paste.

**Audit trail:** `listings.json` stores every listing ever discovered, with full JD text, scores, and timestamps. Nothing is ever deleted from this file. `reviewed.json` tracks the user's actions separately. Both together form the complete audit trail.

---

### 6.4 Data Layer ✅ COMPLETE

All persistent data lives in `{BND_HOME}/data/`:

#### 6.4.1 listings.json

The master record. Every listing ever discovered, regardless of score:

```json
{
  "id": "abc123",              // hash of company + title + location
  "title": "Senior Product Manager, Growth",
  "company": "Amplitude",
  "location": "Remote",
  "url": "https://boards.greenhouse.io/amplitude/jobs/12345",
  "apply_url": "https://boards.greenhouse.io/amplitude/jobs/12345#apply",
  "source": "greenhouse",
  "description": "Full JD text...",
  "posting_date": "2026-04-03",
  "discovered_at": "2026-04-06T00:15:00Z",
  "comp_range": "$170K - $200K",
  "scores": {
    "composite": 4.2,
    "dimensions": { ... },
    "fit_summary": "..."
  }
}
```

#### 6.4.2 scan-state.json

Tracks run progress for resumability:

```json
{
  "last_run": {
    "started_at": "2026-04-06T00:00:00Z",
    "completed_at": "2026-04-06T00:42:00Z",
    "status": "complete",        // complete | partial
    "operations_used": 38,
    "operations_budget": 50
  },
  "pending_queries": [],         // queries that didn't run (if partial)
  "sources_last_searched": {
    "indeed": "2026-04-06",
    "builtin": "2026-04-06",
    "wellfound": "2026-04-05",   // might be a day behind if batched
    "greenhouse": "2026-04-06",
    "lever": "2026-04-06",
    "ashby": "2026-04-05"
  }
}
```

#### 6.4.3 reviewed.json

The user's review state (see §6.3.3). Separate from listings so the audit trail is clean.

#### 6.4.4 config.yml

All user-configurable settings in one file (see §6.6 for full spec).

---

### 6.5 Scheduling & Credit Management ✅ COMPLETE

#### 7.5.1 Two Execution Modes

**Manual:** the user runs `/brand-new-day` in Claude Code. The skill executes immediately — searches, scores, generates dashboard. Useful for ad-hoc runs or testing config changes.

**Scheduled:** A cron job triggers the skill overnight. The user wakes up to a fresh dashboard.

Both modes use the same skill code. The only difference is the trigger.

**Current status (v1.4):** Cron is disabled. The v1.3 `site:` approach consumed significant tokens for zero yield, and permission prompts (60+ individual URL entries instead of wildcards) caused token blowout during scheduled runs. Cron will be re-enabled after the JSearch integration is validated and permissions are fixed. Frequency (daily vs. every-other-day) will be decided based on actual JSearch API usage and token cost per run.

#### 7.5.1.1 Credit Schedule

The system assumes a daily rhythm with protected work blocks and an overnight automation window:

| Time Block | Activity | Credit Priority |
|---|---|---|
| Morning work block | Primary daytime work (applications, prep, interviews) | **Protected — scanner must not be running** |
| Afternoon work block | Continued daytime work | **Protected** |
| Evening | Personal time; may use Claude ad-hoc | Low-priority — scanner should avoid |
| Overnight (~10pm – 6am) | **Automation window** | Scanner runs here |
| Pre-morning buffer | Credits regenerating | No activity |

The cron fires at midnight. The scanner must complete (or pause with state saved) well before the user's morning session. With a 50-operation budget, typical runs complete in 30-45 minutes. Even a worst-case run with retries should finish within an hour or two, leaving several hours of credit regeneration before morning. Specific times are user-configurable; the design assumes a single daytime work shift with a fixed overnight automation window.

#### 6.5.2 Credit-Aware Execution

Claude Pro ($20/month) has rolling credit windows. The skill cannot query credit balance directly, so it uses an **operations budget** as a proxy:

```yaml
scheduling:
  operations_budget: 50          # max tool calls per run (may decrease with JSearch — TBD after first run)
  cron_time: "TBD"               # disabled until JSearch integration validated
```

**How it works:**
1. At run start, load `scan-state.json`
2. If there are `pending_queries` from a previous partial run, execute those first (catch-up)
3. Then execute new queries in priority order (highest-signal sources first)
4. After each operation, increment the counter
5. When counter hits `operations_budget`, save remaining queries to `pending_queries` and stop
6. Generate the dashboard with whatever data is available

**Priority order for queries** (if budget forces prioritization):
1. Catch-up queries from previous incomplete run
2. High-signal sources: Greenhouse, Lever (ATS boards = less noise)
3. Broad boards: Indeed, Built In, Wellfound
4. Lower-priority or newly added sources

**Batching across nights:** If 24 queries can't all run in one night's budget, the skill automatically splits them. Example:
- Night 1: queries 1-15 (budget hit), saves queries 16-24 as pending
- Night 2: queries 16-24 (catch-up), then starts fresh queries 1-15
- Net effect: every source gets searched at least every 48 hours

#### 6.5.3 Run Logging

Every run appends to a `run-log.json` for the user to audit if needed:

```json
{
  "run_id": "2026-04-06-001",
  "trigger": "cron",            // or "manual"
  "started_at": "2026-04-06T00:00:00Z",
  "completed_at": "2026-04-06T00:38:00Z",
  "status": "partial",
  "queries_executed": 15,
  "queries_pending": 9,
  "listings_found": 12,
  "listings_new": 7,
  "listings_duplicate": 5,
  "listings_above_threshold": 3,
  "operations_used": 48,
  "errors": []
}
```

---

### 6.6 Configuration ✅ COMPLETE

All configuration lives in a single file: `{BND_HOME}/config.yml`

Full default config:

```yaml
# ============================================================
# Brand New Day — Configuration
# ============================================================
# Edit this file to tune search behavior, scoring, and scheduling.
# Changes take effect on the next run.
# ============================================================

# --- Search ---
keywords:
  titles:
    - "Product Manager"
    - "Director of Product"
    - "Head of Product"
    - "Group Product Manager"
  locations:
    - "remote"
    - "San Diego"
  exclude_titles:
    - "intern"
    - "associate"
    - "junior"
    - "engineer"
    - "designer"
    - "marketing manager"
    - "project manager"
    - "program manager"

sources:
  - name: "JSearch"
    type: "aggregator_api"
    enabled: true
    priority: 1    # Primary discovery — broadest coverage
  - name: "Adzuna"
    type: "aggregator_api"
    enabled: true
    priority: 2    # Supplemental — different aggregation source

# --- Scoring ---
scoring:
  hard_gates:
    location_fit:
      pass_keywords: ["remote", "san diego", "anywhere", "distributed", "us-based"]
      fail_action: "score_zero"

  weights:
    seniority_fit: 2.0
    domain_match: 2.0
    growth_plg: 2.0
    platform_architecture: 1.0
    company_stage: 1.0
    role_clarity: 1.0
    people_management: 1.0
    comp_signals: 0.5
    application_friction: 0.5

  threshold: 3.5

# --- Scheduling ---
scheduling:
  cron_time: "TBD"              # disabled until JSearch validated
  operations_budget: 50          # max tool calls per run (may decrease with API approach)
  retry_on_error: true
  max_retries_per_query: 2

# --- Output ---
output:
  dashboard_path: "{BND_HOME}/dashboard.html"
  data_dir: "{BND_HOME}/data"

# --- Profile ---
# Path to the user's resume/career context for scoring
profile_path: "{BND_HOME}/profile.md"
```

---

## 7. Technical Design

### 7.1 Skill Structure ✅ COMPLETE

```
~/.claude/skills/brand-new-day/
├── SKILL.md                    # Skill definition + scoring rubric
└── references/
    └── (Phase 1.5b: profile lives at {BND_HOME}/profile.md, no symlink)

{BND_HOME}/
├── config.yml                  # All user configuration
├── dashboard.html              # Generated output (regenerated each run)
└── data/
    ├── listings.json           # All listings ever found (append-only audit log)
    ├── reviewed.json           # the user's review state per listing
    ├── scan-state.json         # Run progress + batch tracking
    └── run-log.json            # Run history
```

### 7.2 Skill Invocation

**Manual run:**
```
/brand-new-day              # Full scan + score + dashboard
/brand-new-day review       # Mark listings as reviewed
/brand-new-day status       # Show last run summary + pending items
/brand-new-day rescore      # Re-score all unreviewed listings (after config change)
```

**Scheduled run:** Cron triggers a Claude Code session that executes the equivalent of `/brand-new-day`.

**Phase 1.5 additions:**
```
/brand-new-day init         # Validate install, test API key, scaffold data files
/brand-new-day doctor       # Re-run validator on existing install
/brand-new-day reset        # Archive data/ and re-create empty starters
```

### 7.3 Deduplication Strategy

Listings are deduped by a normalized key:

```
id = hash( lowercase(company_name) + lowercase(job_title) + lowercase(normalize(location)) )
```

Where `normalize(location)` strips punctuation and standardizes terms (e.g., "San Diego, CA" → "san diego ca", "Remote - US" → "remote us").

**Cross-platform dedup:** The same role posted on Indeed AND Greenhouse gets one entry. The first-seen source is recorded; the apply URL uses the most direct source (prefer ATS board URL over aggregator URL, since aggregator links sometimes break).

### 7.4 Dashboard Refresh

The dashboard HTML file is regenerated from scratch on every run using current data. It is not incrementally updated. This keeps the generation logic simple and the output always consistent with the data layer.

If no new listings are found, the dashboard still regenerates (showing the "no new listings" state with the below-threshold section still available).

### 7.5 Playwright

**Installed.** Playwright v1.59.1 is installed globally via npm.

**What it does:** Playwright is a browser automation library that can render JavaScript-heavy pages. Some job board pages (Indeed, Wellfound) rely on client-side JavaScript to load listing content. When `WebFetch` returns empty or incomplete results for a page, Playwright can launch a headless Chromium browser to fully render the page before extracting content.

**Not required for basic operation.** Most Greenhouse, Lever, and Ashby board pages serve content in static HTML or have API endpoints. Google search results (via `site:` operators) are accessible without rendering SPAs directly. Playwright is available as a fallback for sources that block or fail with standard fetching.

**When it kicks in:** If a specific source consistently returns empty/blocked results via WebFetch, the skill can route that source's fetches through Playwright instead. This is a per-source decision, not a blanket switch.

---

## 8. Phase 1.5 — GitHub Alpha Packaging

Phase 1 shipped a working single-user pipeline on the user's machine. Phase 1.5 turns that pipeline into a **public, replicable GitHub alpha** that another technically-capable user could install and run against their own profile.

This is not a scope expansion of the scanner itself. It is a packaging, security, and configuration refactor. The scanner's behavior, scoring engine, sources, and dashboard are inherited from Phase 1. What changes is where user-specific data lives and how a new user sets it up.

### Why public repo

Public adds visibility during the user's active job search — the repo itself becomes a portfolio artifact that hiring managers can read. Public also forces discipline: any data or secret in history is permanent, which pushes safeguards to be real on day one rather than aspirational.

### Why "technical folks" audience

Alpha users are expected to be comfortable editing YAML, running `install.sh`, managing a RapidAPI key, and reading a README. No GUI installer, no one-click setup. The rubric is tunable via config but ships calibrated for the user's PM search — non-PM users will need to rewrite scoring prompts in config, and that's acceptable for alpha.

---

### 8.1 Sub-Phase 1.5a — Security + Path Portability

Goal: remove all the user-specific absolute paths and all plaintext secrets from the codebase so that (1) the current local install keeps working and (2) nothing in the codebase blocks going public.

| Task | Description |
|---|---|
| 1.5a.1 | Move JSearch API key from `settings.local.json` curl permission patterns into `.env` (already gitignored). Replace the 4 hardcoded-key curl patterns with wildcard pattern `Bash(curl -s https://jsearch.p.rapidapi.com/*)` |
| 1.5a.2 | Introduce `BND_HOME` environment variable (default: `~/brand-new-day`). All runtime paths resolve via `BND_HOME`, not hardcoded `{BND_HOME}/` |
| 1.5a.3 | Update `config.yml` so `output.dashboard_path`, `output.data_dir`, and `profile_path` use `{BND_HOME}` variable substitution |
| 1.5a.4 | Remove vestigial v1.3 ATS permission entries from `settings.local.json` (Greenhouse, Lever, Ashby direct URLs no longer used). Strip absolute paths that reference `<user-home>/` |
| 1.5a.5 | Add `.env.example` documenting required env vars (`RAPIDAPI_KEY`, optional `ADZUNA_APP_ID`/`ADZUNA_APP_KEY`, `BND_HOME`) |

**Exit criteria:** Scanner runs end-to-end with no absolute paths in any tracked file and no secrets outside `.env`.

---

### 8.2 Sub-Phase 1.5b — Rubric & Profile Externalization

#### 8.2.0 Replication-Ready Scan Invocation (shipped 2026-04-22)

Patched in ahead of 1.5b proper. Session 18 hit ~11 permission prompts on a manual scan because the prior invocation pattern (`curl | python3 -c`) combined pipes + inline Python, which the permission matcher couldn't grant reliably. Any future user cloning the public repo would hit the same wall on their first manual run, so this was reclassified as replication hygiene blocking 1.5c's clean first-run UX.

| Task | Description | Status |
|---|---|---|
| 8.2.0.1 | Stdlib-only scan runner at `brand-new-day/bnd-scan.py`. Loads `RAPIDAPI_KEY` from `.env`, 30s timeout, JSON to stdout, distinct exit codes (0/2/3/4/5). Self-documenting permission patterns in header. | ✅ |
| 8.2.0.2 | SKILL.md "Required Permissions" section + no-pipe hard rule + updated invocation examples in §Search Behavior and Step 2 | ✅ |
| 8.2.0.3 | `settings.local.json` — added `Bash(python3 brand-new-day/bnd-scan.py:*)` (relative) + absolute-path fallback; removed 3 obsolete curl wildcards | ✅ |
| 8.2.0.4 | `brand-new-day/bnd-hash.py` stdlib helper: takes company/title/location args, prints 8-char dedup ID. Replaces inline `python3 -c` hashlib calls. | ✅ (Patch 2) |
| 8.2.0.5 | `brand-new-day/bnd-render-dashboard.py` stdlib helper: reads `data/listings.json` + `data/run-log.json`, regenerates `dashboard.html` by replacing only `LISTINGS` and `RUN_LOG` blocks. Preserves CSS/HTML/JS verbatim. | ✅ (Patch 2) |
| 8.2.0.6 | SKILL.md scan procedure rewired: Step 3.3 → `bnd-hash.py`; Step 5 → `bnd-render-dashboard.py`; Steps 3.6/3.7/4/6 → Claude native Read/Write/Edit (no inline `python3 -c` or heredoc scripts). Required Permissions section updated with hard rule against inline python. | ✅ (Patch 2) |
| 8.2.0.7 | `settings.local.json` — added relative + absolute patterns for `bnd-hash.py` and `bnd-render-dashboard.py` | ✅ (Patch 2) |

**Exit criterion (met — Patch 1):** Manual scan dry-run produces valid JSON output with zero permission prompts from the JSearch call.
**Exit criterion (Patch 2):** Full manual scan (`/brand-new-day`) completes end-to-end with zero permission prompts — no inline python in any step.

#### 8.2.1 Rubric & Profile Externalization

Goal: move every the user-specific calibration out of `SKILL.md` prose and into `config.yml` + `profile.md`, so the skill becomes a generic execution engine driven by data.

| Task | Description |
|---|---|
| 1.5b.1 | Extract 10-dimension scoring rubric from SKILL.md prose into structured `config.yml` blocks. Each dimension gets: name, weight, score-5 description, score-3 description, score-1 description, optional `hard_gate: true/false` |
| 1.5b.2 | Generalize hard gates from single `location_fit` field to a named-filter list. Each entry: `name`, `pass_keywords` (or `pass_expression`), `fail_action` (score 0 / skip). Alpha ships with `location_fit` as default; users can add `visa_sponsorship`, `comp_floor`, etc. |
| 1.5b.3 | Move all keyword lists (titles, exclusions, locations, comp bands) from SKILL.md prose to `config.yml` |
| 1.5b.4 | Rewrite SKILL.md to read scoring rubric, hard gates, and profile dynamically from config. Remove all "the user" references — replace with generic addressee or `{user}` |
| 1.5b.5 | Change `profile_path` default from a cross-skill reference (an external one-sheet generator's resume file) to `{BND_HOME}/profile.md`. Remove cross-skill coupling. |
| 1.5b.6 | Create `profile.md.example` template with sections: Background, Target Role, Hard Requirements, Nice-to-Haves, Comp Floor, Locations. The user's actual profile lives at `{BND_HOME}/profile.md` (gitignored) |

**Exit criteria:** Changing target role from "Senior PM in SaaS" to "Staff Engineer in Austin" requires editing `config.yml` and `profile.md` only. No skill file changes.

---

### 8.3 Sub-Phase 1.5c — Repo Packaging

Goal: create the GitHub repo with proper layout, license, and safeguards so the project is publishable without leaking personal data.

| Task | Description |
|---|---|
| 1.5c.1 | Create `brand-new-day` GitHub repo. License: MIT. Public visibility |
| 1.5c.2 | Repo layout: `skill/` (SKILL.md + references/), `runtime/` (config.yml.example, profile.md.example, fetch-page.js, empty data/ starters, dashboard template), `install.sh`, `README.md`, `.env.example`, `.gitignore` |
| 1.5c.3 | `.gitignore` covers: `.env`, `BND_HOME/` contents, `data/*.json` (except `.gitkeep`), `dashboard.html`, `profile.md`, `*.local.json` |
| 1.5c.4 | Pre-commit hook (documented, not forced) that greps for known API key patterns (`x-rapidapi-key:`, `AKIA`, etc.) and blocks commit on match |
| 1.5c.5 | `README.md` with: what it is, prerequisites (Claude Code, Node, RapidAPI account), install (`./install.sh`), customize (`config.yml` + `profile.md`), cron setup, troubleshooting |
| 1.5c.6 | Security section in README: explicit warning that this is alpha, that public forks must reset their own `.env`, that resume data must not be committed |
| 1.5c.7 | Dashboard template decoupled from the user's data — renders from whatever `listings.json` contains. Empty state handled gracefully |

**Exit criteria:** Fresh clone of public repo contains zero the user-specific content. `git log` contains zero leaked secrets or personal data. Repo is buildable by another user following README.

---

### 8.4 Sub-Phase 1.5d — Install + Onboarding

Goal: reduce first-run setup to a single script and a validator, so a new user is producing scored listings within 15 minutes.

| Task | Description |
|---|---|
| 1.5d.1 | `install.sh`: copies `skill/` → `~/.claude/skills/brand-new-day/`, scaffolds `BND_HOME` directory, copies `config.yml.example` → `config.yml`, copies `profile.md.example` → `profile.md`, prompts interactively for RapidAPI key and writes `.env`. Idempotent |
| 1.5d.2 | `/brand-new-day init` skill subcommand: validates `config.yml` parses, confirms `BND_HOME` exists and is writable, confirms `.env` has `RAPIDAPI_KEY`, tests API key with single JSearch call, writes starter `listings.json` / `scan-state.json` / `run-log.json` / `reviewed.json` / `api-usage.json` / `credit-ledger.json` |
| 1.5d.3 | `/brand-new-day doctor` subcommand: re-runs validator against an existing install, reports anything broken |
| 1.5d.4 | Cron setup docs in README: both `mcp__scheduled-tasks` path (for users with that MCP) and `launchd` plist template (macOS) as fallback. Linux `cron` and `systemd timer` variants stretch-goal |
| 1.5d.5 | `/brand-new-day reset` subcommand: archives current `data/` to `data/archive-{date}/`, re-creates empty starters. For users wanting to restart their pipeline |

**Exit criteria:** On a fresh Mac with Claude Code and Node installed, a user can clone the repo, run `install.sh`, edit `profile.md` + 3 lines of `config.yml`, run `/brand-new-day init`, and see scored listings within 15 minutes. Validated by the user re-installing on a clean `BND_HOME` path.

---

### 8.5 Out of Scope for Phase 1.5

Explicitly deferred to Phase 2 or later:

- Adzuna source (stays disabled in config, re-enabled in Phase 2)
- Multi-source abstraction beyond JSearch (no adapter interface for future LinkedIn/Workday/etc.)
- Pre-built non-PM rubric templates (Designer, Engineer, Data, Sales) — alpha ships with the PM rubric; users adapt it themselves
- Windows or Linux install parity — macOS is the supported alpha target
- GUI config editor / web onboarding
- Interview-prep handoff (still Phase 2, inherited from v1.4)
- Cover letter generation (still Phase 2)
- Scoring feedback loop (still Phase 2)
- Notion push (still Future)

---

### 8.6 Security Safeguards for Public Repo

Non-negotiable before going public:

1. **No secrets in history.** `.env` never tracked. `settings.local.json` API key removed *before* first public commit. Run `git log -p | grep -i rapidapi` — must return nothing.
2. **No personal data in history.** the user's actual `profile.md`, `listings.json`, `reviewed.json`, `dashboard.html`, `credit-ledger.json` never tracked. `data/` ships with `.gitkeep` placeholders only.
3. **.gitignore verified before first commit.** Dry-run test: populate `BND_HOME` with real data, run `git status`, confirm nothing personal appears as untracked-but-would-be-added.
4. **Pre-commit hook recommended in README.** Grep for known secret patterns.
5. **README warning.** Explicit callout that forks must reset `.env` and profile before pushing anywhere.

---

### 8.7 Phase 1.5 Success Metrics

Phase 1.5 is successful if:

1. The user's current install continues working throughout the refactor (no regressions).
2. A second user (technical, PM or adjacent) can clone the repo and reach first scored listings in under 15 minutes.
3. The repo can be made public without leaking any secret or personal data, verified by the user before first push.
4. Changing target role parameters requires zero code changes — config + profile only.

---

### 8.8 Phase 1.5 Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| API key accidentally committed during refactor | Medium | 1.5a done first and verified before any public push. Pre-commit hook docs in 1.5c. |
| the user's local install breaks during 1.5a/b refactor | Medium | Each sub-phase has explicit exit criteria. Test scanner end-to-end after each. |
| Resume/profile data ends up in git history | Medium | `.gitignore` dry-run test in 1.5c.3. No public push until verified. |
| Rubric externalization breaks scoring calibration | Low | Compare scoring output against current v1.4 baseline on same listings before merging 1.5b |
| Alpha users struggle with install despite `install.sh` | Medium | `/brand-new-day doctor` subcommand in 1.5d.3. README troubleshooting section |
| JSearch ToS violation from public tool usage | Low | Each user brings own API key and respects their own rate limits. Not scraping, using published API |

---

### 8.9 Phase 1.5 Resolved Decisions

1. **Repo name:** `brand-new-day`
2. **Sources in alpha:** JSearch only. Adzuna remains disabled until Phase 2.
3. **Cron setup:** Manual only. README documents both `mcp__scheduled-tasks` and `launchd` paths. `/brand-new-day init` does not touch cron.
4. **Example listings:** Not shipped. Fresh install renders an empty dashboard until first scan completes.

---

### 8.10 Phase 1.5 Sequencing & Estimates

| Sub-Phase | Est. Sessions | Notes |
|---|---|---|
| 1.5a — Security + path portability | 1 session | Small, focused refactor. Security-sensitive — should ship fast. |
| 1.5b — Rubric & profile externalization | 1–2 sessions | Rubric externalization is the largest surface. Risk of scoring drift. |
| 1.5c — Repo packaging | 1 session | Mostly mechanical — new repo, gitignore, README. |
| 1.5d — Install + onboarding | 1–2 sessions | `install.sh` + init validator are real code. Cron doc takes care. |

**Total estimate: 4–6 sessions.** Each sub-phase is independently sign-off-able.

---

## 9. Integration Points

### 9.1 External One-Sheet Generator

**No copy-paste.** The data layer stores everything an external one-sheet generator needs (company, role title, JD URL, full JD text). The handoff works like this:

1. The user opens Claude Code and says: `prep me for listing 3` (or `prep me for the Amplitude role`)
2. The brand-new-day skill resolves the reference → loads the listing from `listings.json`
3. Passes company name, role title, JD URL, and JD text directly to the one-sheet generator
4. The generator produces the one-sheet as usual

**Alternatively:** `/brand-new-day prep 3` or `/brand-new-day prep amplitude` — a sub-command that triggers the one-sheet generator with listing data pre-loaded. The user never types a company name, role title, or URL that the system already knows.

The dashboard's `[Prep One-Sheet]` button displays the natural-language command the user can say in Claude Code (e.g., "prep me for the Amplitude Senior PM role"). This isn't a copy-paste requirement — it's a reminder of what to ask for, since Claude Code is conversational. The listing data flows through the data layer, not through the user's clipboard.

This integration assumes a separate one-sheet generation tool exists in the user's environment. The public alpha does not bundle one.

### 9.2 Cover Letter Generation (Phase 2)

Same zero-copy-paste pattern:
- `cover letter for listing 3` or `/brand-new-day cover-letter amplitude`
- Reads the user's profile + the stored JD text from `listings.json`
- Generates a tailored cover letter
- Outputs as HTML (matching the design system) to `{BND_HOME}/cover-letters/`

Not in scope for Phase 1. Noted here as a planned integration point.

### 9.3 Notion (Future)

A future integration could push high-scoring listings directly to a Notion Kanban board as cards. Deferred because Notion MCP is token-expensive.

---

## 10. Phases & Roadmap

### Phase 1 — Core Scanner ✅ COMPLETE

| Component | Deliverable | Status |
|---|---|---|
| Skill definition | `~/.claude/skills/brand-new-day/SKILL.md` | ✅ |
| Configuration | `config.yml` with defaults | ✅ |
| Search engine | Keyword-based search via JSearch/Adzuna APIs | ✅ |
| Scoring engine | 10-dimension weighted scoring with hard gates | ✅ |
| Data layer | listings.json, reviewed.json, scan-state.json, run-log.json | ✅ |
| Dashboard | Local HTML, card-based, light mode, zero-copy-paste actions | ✅ |
| Scheduling | Cron (overnight, frequency TBD) + manual `/brand-new-day` | ✅ |
| Credit management | Operations budget with cross-night catch-up | ✅ |
| Review workflow | In-page buttons (localStorage → sync on next run) + `/brand-new-day review` CLI fallback | ✅ |
| Dedup | Cross-platform deduplication | ✅ |

### Phase 1.5 — GitHub Alpha Packaging (This Build)

| Component | Deliverable | Sub-Phase |
|---|---|---|
| Security + path portability | `.env`, `BND_HOME`, strip absolute paths | 1.5a |
| Rubric externalization | `config.yml` scoring blocks, `profile.md` | 1.5b |
| Repo packaging | GitHub repo, `.gitignore`, `README.md`, MIT license | 1.5c |
| Install + onboarding | `install.sh`, `/brand-new-day init`, `doctor`, `reset` | 1.5d |

### Phase 2 — Enhancements

| Feature | Description |
|---|---|
| Interview-prep handoff | `/brand-new-day prep [id]` triggers one-sheet generation from stored data. Deferred from Phase 1 — data layer supports it, wiring deferred until scanner produces reliable listings. |
| Direct ATS API monitoring | Targeted company monitoring via Workday/Lever/Ashby/Greenhouse APIs with curated seed list |
| Cover letter generation | `/brand-new-day cover-letter [id]` — generates tailored cover letter from stored JD |
| Scoring feedback loop | "This was a good/bad match" feedback that tunes weights over time |
| Additional sources | PM Job Board, Glassdoor, ZipRecruiter as needed |
| Notion push | High-scoring listings → Kanban board cards |
| Smarter dedup | Use JD text similarity (not just title+company hash) to catch reposted roles |

### Future — Full Automation

| Feature | Description |
|---|---|
| LinkedIn automation | Automated processing of LinkedIn job alerts (method TBD — API, email parsing, or browser automation) |
| Google Alerts automation | Parse incoming alert emails or replicate the search queries directly |
| Auto-cover-letter | Generate and attach cover letters for 5-score listings |
| Analytics | Weekly/monthly summary of search patterns, response rates, market trends |
| Mobile dashboard | Push dashboard to a hosted location or Notion for phone access |

---

## 10.1 Build Estimate — Phase 1 ✅ COMPLETE

Phase 1 shipped in 14 sessions. Estimate was 8-10; actual was 14, primarily due to the v1.3 → v1.4 discovery source pivot (4 sessions diagnosing stale URL problem and implementing JSearch replacement).

| Component | Estimated Sessions | Actual |
|---|---|---|
| Skill definition (SKILL.md) | 1 | 1 |
| Config + data layer setup | 1 | 1 |
| Search engine | 2-3 | 5 (includes v1.3 WebSearch + pivot to JSearch) |
| Scoring engine | 1-2 | 2 |
| Dashboard HTML generation | 1-2 | 2 |
| Interview-prep handoff | 1 | Deferred to Phase 2 |
| Cron scheduling | 1 | 1 (cron disabled pending JSearch validation) |
| End-to-end testing + tuning | 2-3 | 2 |

---

## 11. Constraints & Risks

### Constraints

| Constraint | Impact | Mitigation |
|---|---|---|
| $20/mo Claude Pro plan | Limited credits per session window | Operations budget, overnight scheduling, cross-night batching |
| No LinkedIn automation | Misses LinkedIn-only postings | Manual LinkedIn stays in workflow; system remembers this is a future target |
| No auto-apply | the user still applies manually | Dashboard minimizes friction with direct apply links |
| Local-only output | No mobile access to dashboard | HTML is phone-responsive if the user opens it via file sharing or localhost |
| WebSearch rate limits | Google may throttle rapid searches | Spread queries with brief pauses; prioritize high-signal sources |

### Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Job board blocks WebFetch | Medium | Listings missed from blocked source | Fall back to Google cache; add Playwright for that source; degrade gracefully |
| Scoring drift (good roles scored low) | Medium | the user misses relevant roles | Below-threshold section on dashboard; periodic manual review of filtered listings; feedback loop in Phase 2 |
| Credit budget too tight | Low-Medium | Runs don't complete | Conservative default (50 ops); cross-night catch-up; tune based on actual usage |
| Dedup false positives | Low | Same role at same company in different teams merged | Include team/department in hash if available in JD |
| Stale listings surfaced | ~~Low~~ **Realized** | v1.3 `site:` approach returned 80-100% stale URLs across 4 runs. v1.4 mitigates by switching to aggregator APIs that return only live postings. Residual risk: aggregator index lag (typically <48h). | Use `date_posted` filter in API queries; exclude listings older than 30 days |
| API free tier limits | Medium | JSearch: 1,000 req/mo. Adzuna: ~250 req/day. Exceeding limits blocks discovery. | Conservative query strategy (~8 queries/run), track usage in scan-state.json, alert if approaching 80% of monthly quota |

---

## 11.1 Credit Observability

Brand New Day tracks credit consumption at two levels:

### Per-Run Tracking (built into the scanner)

Every scan run logs its operations count to `run-log.json` (see §6.5.3). This tells the user how much each nightly scan costs and whether the operations budget needs tuning.

### Project-Level Credit Ledger (meta-tracking)

A separate `credit-ledger.json` in the data directory tracks credit usage across *all* brand-new-day-related activity — not just scans, but also building the tool, tuning scoring, generating one-sheets from scanner data, etc.

**File:** `{BND_HOME}/data/credit-ledger.json`

```json
{
  "entries": [
    {
      "date": "2026-04-07",
      "activity": "PRD revision v1.2",
      "type": "build",
      "estimated_tokens": 15000,
      "notes": "PRD edits based on v1.1 feedback"
    },
    {
      "date": "2026-04-08",
      "activity": "Nightly scan",
      "type": "scan",
      "operations": 42,
      "listings_scored": 8,
      "notes": "Auto-logged by scanner"
    }
  ],
  "totals": {
    "build_sessions": 1,
    "scan_runs": 0,
    "total_operations": 0
  }
}
```

**Activity types:**
- `build` — sessions spent building or modifying the scanner itself
- `scan` — nightly or manual scan runs
- `prep` — one-sheets generated from scanner data
- `maintenance` — config tuning, bug fixes, scoring adjustments

This gives the user a running picture of total investment over weeks and months. Claude updates the ledger at the end of each relevant session.

---

## 12. Glossary

| Term | Definition |
|---|---|
| **ATS** | Applicant Tracking System — software companies use to manage job postings and applications. Greenhouse, Lever, and Ashby are ATS platforms. |
| **Hard gate** | A scoring dimension where failure means automatic score of 0, regardless of other dimensions. Currently only Location Fit. |
| **Operations budget** | The maximum number of WebSearch + WebFetch tool calls allowed per run. Proxy for credit consumption. |
| **Composite score** | Weighted average of all dimension scores, normalized to a 0-5 scale. |
| **Catch-up** | When a run doesn't complete all queries, the remaining queries are saved and executed first on the next run. |
| **PLG** | Product-Led Growth — a go-to-market strategy where the product itself drives acquisition, activation, and retention. |
| **DXP** | Digital Experience Platform — enterprise software for managing digital content and customer experiences across channels. |
| **BND_HOME** | Environment variable pointing to the Brand New Day runtime directory. Default: `~/brand-new-day`. All runtime paths resolve via this variable. |

---

## Appendix A: Profile Summary (for Scoring Context)

Profile-specific scoring calibration is now externalized to `profile.md` (per Phase 1.5b, decision D-016). See `profile.md.example` in the public repo for the structural template — sections include Background, Target Role, Hard Requirements, Nice-to-Haves, Comp Floor, and Locations.

The calibration originally shipped here was tuned for a senior PM in SaaS / CMS / DXP / platform domains. Users adapting Brand New Day to their own search rewrite both the rubric (`config.yml`) and profile (`profile.md`) for their target role. The original profile content has been redacted from this published version of the PRD; see the `profile.md.example` template for the field structure.

---

## Appendix B: AI Lineage & Inspiration Sources

This PRD was co-authored by Eric Broadwater and Claude (Anthropic). The following external sources informed the design:

**santifer/career-ops** ([github.com/santifer/career-ops](https://github.com/santifer/career-ops))
- **Borrowed:** Config-driven architecture, weighted scoring rubric concept, skill-based execution model
- **Rejected:** Multi-agent orchestration (too token-heavy for $20 Claude Pro plan), auto-apply (wrong approach for PM-level roles), PDF generation, LinkedIn scraping
- **Original analysis:** 2026-04-06

**Masterjx9/OpenPostings** ([github.com/Masterjx9/OpenPostings](https://github.com/Masterjx9/OpenPostings))
- **Borrowed (patterns only, no code — repo has no license):** Direct ATS API endpoint patterns for Workday, Lever, Ashby, Greenhouse. 24-hour TTL pruning concept. Random company ordering for rate limit distribution.
- **Rejected:** Regex HTML parsing (fragile), single-file architecture, MCP auto-apply (out of scope)
- **Key insight:** Direct ATS APIs return only live postings, completely bypassing the stale URL problem. Documented endpoints fed directly into v1.4 §6.1.2 (Direct ATS APIs table).
- **Original analysis:** 2026-04-14

**JSearch (RapidAPI)**
- **Adopted as primary discovery source (v1.4):** Title-first keyword search returning structured JSON of live postings. 1,000 req/mo free tier. Aggregates Google Jobs index (Indeed, LinkedIn, Glassdoor, ZipRecruiter, company career sites).
- **Key insight:** Queries the same Google Jobs index that the v1.3 `site:` approach was trying to use, but returns only live postings as structured data — same source, no stale URLs.
- **Original analysis:** 2026-04-14

**Adzuna API**
- **Adopted as supplemental discovery source (v1.4):** Different aggregation pipeline from JSearch. ~250 req/day free. 12 countries.
- **Notable:** An Adzuna MCP server exists (`folathecoder/adzuna-job-search-mcp`) for potential direct Claude Code integration.
- **Original analysis:** 2026-04-14

**Dead ends investigated (session 10):**
- **Indeed API** — shut down. Sponsored Jobs API requires ad spend.
- **ZipRecruiter API** — deprecated March 2025.
- **LinkedIn API** — closed to new partners.
- **Wellfound / Built In** — no public APIs. Wellfound confirmed login-walled.

Future AI-inspired design decisions will be logged here as they arise.

---

## Appendix C: Decision Log

Abridged entries — see linked memory files for full context where noted.

| # | Date | Decision | Why | Alternatives Considered |
|---|---|---|---|---|
| D-001 | 2026-04-07 | Source fetch priority: API > WebFetch > Playwright > snippet-only | APIs return structured JSON, no parsing needed. Playwright is slow and token-heavy. Snippet-only is a graceful degradation, not a preferred path. | Playwright-first (rejected: too expensive per listing), WebFetch-only (rejected: many sites return 403/404) |
| D-002 | 2026-04-07 | LinkedIn excluded from Phase 1, stays manual | LinkedIn's anti-bot enforcement and TOS make automation risky. Most PM roles post there, so the cost of an account ban is too high. | Evaluated `toadlyBroodle/linkedin-easy-apply` — auto-applier, not a scanner; single commit; TOS risk. Build own Playwright scraper in Phase 2. |
| D-003 | 2026-04-07 | Scoring: 9 weighted dimensions + location hard gate, threshold 3.5 | Matches the user's actual mental evaluation process. Weights tunable in config.yml without code changes. Hard gate prevents wasting time on non-remote roles. | Single composite score (rejected: loses diagnostic value), pass/fail only (rejected: too coarse) |
| D-004 | 2026-04-07 | Dashboard as single self-contained HTML file | No build step, no dependencies, opens in any browser, works offline. Keeps complexity low for a personal tool. | React SPA (rejected: overkill), Notion database (rejected: harder to customize, can't run JS), static site generator (rejected: unnecessary build step) |
| D-005 | 2026-04-07 | Design system: DM Sans + DM Mono, card-based, light mode | Matches the interview-prep one-sheet design system for visual consistency across the user's tools. | Tailwind (rejected: requires build), dark mode (rejected: print-unfriendly) |
| D-006 | 2026-04-07 | Renamed project to "Brand New Day" | the user's preference — the name signals a daily fresh-start ritual, not a mechanical scanning tool. | Kept "Job Scanner" (rejected: too generic) |
| D-007 | 2026-04-07 | Greenhouse: use board listing endpoint for discovery, not WebSearch URLs | WebSearch returns stale job IDs that 404 on the API. The `/v1/boards/{company}/jobs` endpoint returns current listings reliably. Discovered during scoring engine test. | Trust WebSearch URLs directly (rejected: 404 rate too high) |
| D-008 | 2026-04-07 | Ashby: use WebFetch on public posting pages, not bulk API | Bulk API (`/posting-api/job-board/{company}`) returns a limited subset. Individual job API returns 401. Public pages at `jobs.ashbyhq.com/{company}/{uuid}` are fetchable. | Bulk API only (rejected: missing jobs), individual API endpoint (rejected: 401) |
| D-009 | 2026-04-07 | Below-threshold listings get full action buttons, not mini cards | the user needs override ability — a below-threshold listing might still be worth applying to for reasons the algorithm can't capture. | Mini cards with no actions (rejected: no way to act on overrides) |
| D-010 | 2026-04-07 | Separate "View Posting" link from state actions (Mark Applied, etc.) | Original "Apply →" button was ambiguous — unclear if it changed state or just opened the link. Separating makes intent clear. | Single "Apply" button that does both (rejected: confusing UX) |
| D-011 | 2026-04-14 | Replace WebSearch + `site:` with JSearch API as primary discovery | 4 runs yielded 80-100% stale URLs, 0 new listings on run 4. JSearch queries the same Google Jobs index but returns only live postings as structured JSON. Adzuna as supplemental. | Keep `site:` as primary (rejected: fundamentally broken — Google caches closed postings), direct ATS APIs only (rejected: company-first, not title-first), scraping (rejected: fragile, TOS risk) |
| D-012 | 2026-04-14 | Interview-prep handoff deferred from Phase 1 to Phase 2 | Scanner must produce reliable listings before the handoff is useful. Data layer already supports it; only the wiring is deferred. | Keep in Phase 1 (rejected: no reliable listings to hand off yet) |
| D-013 | 2026-04-14 | Cron disabled, frequency TBD | v1.3 cron caused token blowout (60+ individual URL permission prompts) and zero yield. Will re-enable after JSearch validated and permissions fixed. | Keep daily midnight (rejected: unsustainable with current approach) |
| D-014 | 2026-04-16 | Phase 1.5 scope: packaging only, no scanner feature changes | Phase 1 is functionally complete. Going public adds portfolio value during job search. Keeping 1.5 as packaging-only prevents scope creep and preserves scanner stability. | Add new sources in 1.5 (rejected: premature), keep private (rejected: loses portfolio value) |
| D-015 | 2026-04-16 | `BND_HOME` as path anchor, not hardcoded paths | Enables portability across machines and users without touching skill code. Default is `~/brand-new-day` to distinguish from the user's dev path. | Per-user config override (rejected: more complex), symlink strategy (rejected: fragile) |
| D-016 | 2026-04-16 | Profile decoupled from `interview-prep` skill | Phase 1.5 targets external users who won't have `interview-prep` installed. `{BND_HOME}/profile.md` is self-contained. The user's profile stays in the gitignored runtime dir. | Keep cross-skill coupling (rejected: non-portable), bundle resume in repo (rejected: personal data in public repo) |

*New decisions should be appended here as they arise. Mark superseded decisions with ~~strikethrough~~ and link to the replacement.*

---

## Appendix D: v1.3 → v1.4 Changelog

**Date:** 2026-04-14

**Summary:** v1.4 replaces the broken WebSearch + `site:` discovery strategy with job aggregator APIs (JSearch, Adzuna) and reflects the current state of Phase 1 after 4 test runs and 10 sessions of development.

### Changed

- **§6 System Architecture** — Search engine box updated from "WebSearch by keyword" to "JSearch API (primary) + Adzuna (supplemental)"
- **§6.1.2 Sources** — Replaced 6-source `site:` table with aggregator API strategy (JSearch primary, Adzuna supplemental, direct ATS APIs documented for Phase 2)
- **§6.1.3 Query Construction** — Updated from `title × source site:` to JSearch API params. ~8 queries/run (down from 24)
- **§6.1.4 Result Processing** — Updated for structured API responses instead of WebSearch URL scraping
- **§6.1.5 Adding Sources** — Simplified for API-based approach
- **§6.1.6 Source Discovery** — Updated to reflect aggregator-first discovery
- **§6.5 Scheduling** — Acknowledged cron is disabled, frequency TBD pending JSearch validation
- **§6.6 Config** — Updated sources and scheduling defaults
- **§11 Risks** — "Stale listings" upgraded from Low to Realized; added "API free tier limits" risk

### Moved

- **Interview-prep handoff** — Moved from Phase 1 (§10) to Phase 2. Data layer supports it; wiring deferred until scanner produces reliable listings.

### Added

- **Direct ATS API endpoints** documented in §6.1.2 (Workday, Lever, Ashby, Greenhouse) for Phase 2 targeted monitoring
- **Decisions D-011 through D-013** in Appendix C
- **This changelog** (Appendix D)

### Deprecated

- **WebSearch + `site:` operators** — Retained as optional fallback, no longer primary. 80-100% stale URL rate across 4 runs.

---

## Appendix E: v1.4 → v1.5 Changelog

**Date:** 2026-04-16

**Summary:** v1.5 adds Phase 1.5 — GitHub alpha packaging — to the complete Phase 1 scope. All Phase 1 content is preserved verbatim. v1.5 is now the authoritative self-contained document replacing the prior delta-doc format.

### Added

- **Section 8: Phase 1.5 — GitHub Alpha Packaging** — Sub-phases 1.5a through 1.5d with full task tables, exit criteria, security safeguards, resolved decisions, and sequencing/estimates
- **§8.1–8.4** — Detailed task breakdowns for each sub-phase
- **§8.5** — Out-of-scope items for Phase 1.5
- **§8.6** — Security safeguards for public repo
- **§8.7** — Phase 1.5 success metrics
- **§8.8** — Phase 1.5 risks
- **§8.9** — Phase 1.5 resolved decisions
- **§8.10** — Sequencing and session estimates
- **`BND_HOME`** added to Glossary (§12)
- **Decisions D-014 through D-016** in Appendix C
- **This changelog** (Appendix E)

### Updated

- **Header metadata** — Version 1.5, date 2026-04-16, status "Draft — pending sign-off", supersedes note
- **§1 Executive Summary** — Phase 1 complete status note
- **§7.2 Skill Invocation** — Added Phase 1.5 subcommands (`init`, `doctor`, `reset`)
- **§10 Phases & Roadmap** — Phase 1 marked ✅ COMPLETE with actual vs. estimated sessions; Phase 1.5 column added
- **§10.1 Build Estimate** — Updated with actuals

### Unchanged

- All Phase 1 scope, architecture, scoring engine, sources, dashboard design, data layer, configuration, dedup strategy, Playwright integration, integration points, constraints, risks, credit observability, glossary, Appendix A, Appendix B, Appendix C (D-001–D-013), Appendix D

---

### Patch 1 — 2026-04-22

**§8.2.0 Replication-Ready Scan Invocation** added as a pre-1.5b patch. Documents three items shipped in session 18 (Mon 2026-04-22): `brand-new-day/bnd-scan.py` stdlib scan runner, SKILL.md "Required Permissions" + no-pipe rule, `settings.local.json` permission patterns. Reclassified from 1.0 cron-gate work to 1.5c replication hygiene after confirming the scheduled task already had blanket Bash approval; the prompts were from a manual interactive scan. Header `Status` row updated; new `Patches` row added.

### Patch 2 — 2026-04-22 (same session, post-1.5b)

**§8.2.0 extended** with tasks 8.2.0.4–8.2.0.7. Problem: after 1.5b shipped, a manual `/brand-new-day` scan hit 7 permission prompts — all from inline `python3 -c` and `python3 << 'PYEOF'` heredoc invocations used for dedup-ID generation, listings.json/reviewed.json appends, scan-state/run-log/api-usage updates, and dashboard regeneration. Same permission-matcher bug class as Patch 1 (braces/newlines in quoted args cannot be pattern-permitted), applied to the non-JSearch parts of the scan flow. Fix combines two new stdlib helpers (`bnd-hash.py`, `bnd-render-dashboard.py`) with a rewrite of SKILL.md to use Claude's native Read/Write/Edit tools for JSON file work. Cron scans were never affected (blanket Bash approval); the fix is purely for manual/replication UX ahead of 1.5c.

### Patch 3 — 2026-04-27 (Phase 1.5c shipped + pre-commit hook hardening)

**§8.3 (1.5c) shipped to public.** Repo: `https://github.com/ericbroadwater/brand-new-day` — public, MIT licensed, 16 files, single root commit `32835c2`. All §8.6 safeguards re-verified pre-push (zero secrets, zero personal paths, two intentional the user residues in LICENSE copyright + README byline). §8.3 exit criteria verified post-push via fresh `/tmp` clone.

**Pre-commit hook hardening (related to §8.3.4 + §8.6.4).** First commit attempt was blocked by the hook on three false positives: (1) `"x-rapidapi-key"` HTTP header field name in `runtime/bnd-scan.py` (legitimate API call construction, not a literal key); (2) `X-RapidAPI-Key:` in README's user-facing `git log | grep` instruction; (3) `RAPIDAPI_KEY=[A-Za-z0-9]` self-match against the hook's own pattern definitions. Two-part fix shipped in the same commit:
- **Pattern tightening:** the three RapidAPI patterns now require `[A-Za-z0-9]{30,}` after the prefix (real RapidAPI keys are ~50 chars, all alphanum, no underscores). The `[` character in the old loose pattern definitions can no longer self-match because brackets aren't in `[A-Za-z0-9]`.
- **Path exclusion:** `git diff --cached -U0 -- ':!.githooks/pre-commit' ':!*.example'` — the hook now skips itself (defense against future loose-pattern additions self-matching) and any `*.example` files (placeholder values like `your_rapidapi_key_here` would otherwise false-positive on the original pattern).

The hook fix benefits every downstream user, not just the user — without it, anyone editing the hook file or extending `.env.example` would hit the same false positives on their first commit. Caught and fixed pre-publication, which is exactly what the staged-then-tested approach is for.

**Cron permission fix (separate from PRD scope).** Earlier in the same session, the global `~/.claude/settings.json` was extended with broader Bash allowlist patterns (`python3 *`, `cd {BND_HOME}*`, `node fetch-page.js*`, `wc -l *`) after the AM cron stalled on an inline `python3 -c` permission prompt and timed out into an Anthropic API overload. Not a code change — settings only — but documented here for cross-reference with the project memory's `feedback_bnd_cron_permission_loop.md`.

**Backlog items surfaced (open, not 1.5c-blocking):**
- Run-log mislabel: manual scans on a day a scheduled run was supposed to fire get logged as `trigger: scheduled` with a midnight `started_at`. SKILL.md run-logging bug. Candidate for 1.5d cleanup.
- `gh repo create --license` flag is incompatible with `--source`. Documenting the publish flow for users (1.5d.4 candidate) should drop the `--license` flag and rely on the `LICENSE` file in the source.

### Patch 4 — 2026-04-27 (Phase 1.5d shipped — Phase 1.5 complete)

**§8.4 (1.5d) shipped.** Commit `7545c2d` pushed to `github.com/ericbroadwater/brand-new-day`. Two files changed: `install.sh` (stub → real, +154 lines) and `skill/SKILL.md` (+59 lines). Phase 1.5 is now fully complete (1.5a + 1.5b + 1.5c + 1.5d).

**Tasks shipped:**
- **1.5d.1 (install.sh):** real idempotent installer per spec, with one deliberate scope adjustment — also creates the empty starter JSON files in `data/` (`listings.json` / `reviewed.json` / `scan-state.json` / `run-log.json` / `api-usage.json` / `credit-ledger.json`). Per spec these were init's responsibility (1.5d.2), but moving them into install.sh ensures the installer is self-contained: a user who skips `init` can still run a first scan without missing-file errors. Tradeoff documented and accepted ("Option Y" in the session 22 plan). Idempotency verified across three test runs (fresh, re-run, re-run with API key).
- **1.5d.2 (init):** new SKILL.md section `/brand-new-day init` plus a shared "Validation Procedure" (5 checks: config parses, BND_HOME writable, RAPIDAPI_KEY present + non-placeholder, JSearch test call works, profile loads non-empty). Reuses existing `bnd-scan.py` for the JSearch test — no new scripts, fits the §8.2.0 P2 "no inline python" hard rule.
- **1.5d.3 (doctor):** new SKILL.md section `/brand-new-day doctor` running the same Validation Procedure plus data-layer JSON sanity checks. Read-only by design — never overwrites or repairs files.
- **1.5d.5 (reset):** new SKILL.md section `/brand-new-day reset` archiving `data/*.json` to `data/archive-{YYYY-MM-DD}/` then re-creating empty starters. Confirmation prompt before any move; never silent.
- **1.5d.4 (cron docs):** already shipped in 1.5c (README lines 107–153 cover both `mcp__scheduled-tasks` and `launchd` plist with full template). Marked complete in this patch for accounting purposes; no work needed in 1.5d.

**Frontmatter updated** so `/brand-new-day init`, `/brand-new-day doctor`, and `/brand-new-day reset` route to the skill (added to the description's trigger list).

**Verification:** Pre-push, fresh end-to-end install run against an ephemeral `/tmp` BND_HOME: install.sh exit 0, all 15 expected files created, skill file synced. The §8.4 exit criterion ("Validated by the user re-installing on a clean `BND_HOME` path") is satisfied at the structural level by this automated test; the live `/brand-new-day init` smoke test on the user's actual install is a manual follow-up step requiring his Claude Code session.

**Pre-commit hook performance:** today's earlier hook hardening (Patch 3) held up — the 1.5d commit passed the hook cleanly with no manual `--no-verify` needed.

---

*End of PRD. Phase 1.5 complete 2026-04-27.*
