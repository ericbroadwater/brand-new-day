# PRD v1.5 — Reading Guide

**Full PRD:** `<prd-source-dir>/brand-new-day-prd-v1.5.md`

The PRD exceeds the 10,000 token Read limit. Use `offset` and `limit` to read the section you need. This guide maps sections to line ranges.

**Last refreshed:** 2026-04-27 (after Patch 4 — Phase 1.5 complete). PRD currently 1369 lines.

## How to Use This Guide

Read only what you need for the task at hand. Each row in the chunks table tells you which lines to load and what you'll find there. The task-based navigation section at the bottom maps common work to specific line ranges.

## Recommended Chunks

| Chunk | Lines | Sections | Use when... |
|---|---|---|---|
| Context | 1–100 | §1–§5 | You need goals, problem statement, success metrics, design principles |
| Search | 173–315 | §6.1 | You're working on search queries, sources (JSearch/Adzuna), result processing |
| Scoring | 317–403 | §6.2 | You're working on scoring dimensions, weights, composite calculation |
| Dashboard | 404–507 | §6.3 + §7.3.3 | You're working on dashboard layout, review tracking, state management |
| Data Layer | 508–571 | §6.4 | You're working on JSON schemas (listings, scan-state, reviewed) |
| Scheduling | 572–650 | §6.5 | You're working on cron, credit management, operations budget, run logging |
| Configuration | 651–733 | §6.6 | You're working on config.yml structure and defaults |
| Technical Design | 734–802 | §7 | You need skill structure, invocation, dedup strategy, Playwright notes |
| Phase 1.5 Overview | 803–818 | §8 intro | You need the rationale and audience for the GitHub alpha packaging phase |
| Phase 1.5a | 819–834 | §8.1 | You're working on security, `.env`, `BND_HOME`, path portability |
| Phase 1.5b | 835–870 | §8.2 (incl. §8.2.0 + §8.2.1) | You're working on rubric/profile externalization, config restructure |
| §8.2.0 Replication-Ready Scan | 837–853 | §8.2.0 | You're working on permission-clean scan invocation, helper scripts, no-inline-python rule |
| Phase 1.5c | 871–888 | §8.3 | You're working on repo packaging, gitignore, README, license |
| Phase 1.5d | 889–904 | §8.4 | You're working on `install.sh`, `init`/`doctor`/`reset` subcommands |
| Phase 1.5 Scope | 905–920 | §8.5 | You need the explicit out-of-scope list for Phase 1.5 |
| Phase 1.5 Security | 921–932 | §8.6 | You're verifying public repo security safeguards |
| Phase 1.5 Success | 933–978 | §8.7–§8.10 | You need success metrics, risks, resolved decisions, sequencing/estimates |
| Integration | 979–1009 | §9 | You're wiring interview-prep, cover letter, or Notion integration |
| Phases & Roadmap | 1010–1076 | §10–§10.1 | You need Phase 1/1.5/2/Future scope or Phase 1 actuals vs. estimates |
| Risks & Credits | 1077–1152 | §11–§11.1 | You need constraints, risk table, credit observability spec |
| Glossary | 1153–1167 | §12 | You need a term definition (includes `BND_HOME`) |
| Profile Appendix | 1168–1195 | Appendix A | You need the user's profile signals for scoring calibration |
| Lineage Appendix | 1196–1230 | Appendix B | You need design inspiration sources and what was borrowed/rejected |
| Decision Log | 1231–1257 | Appendix C | You need the full decision log (D-001 through D-016) |
| v1.3→v1.4 Changelog | 1258–1291 | Appendix D | You need the prior version delta for context |
| v1.4→v1.5 Changelog + Patches | 1292–1369 | Appendix E | You need the v1.5 delta — what's new vs. inherited — AND post-sign-off patches 1–4 |
| Patches 1–4 only | 1326–1369 | Appendix E tail | You want only the post-sign-off changes (P1–P4) |

## Example Usage

```
Read(file_path="<prd-source-dir>/brand-new-day-prd-v1.5.md", offset=819, limit=16)
# → Reads §8.1 Phase 1.5a — Security + Path Portability (lines 819–834)
```

```
Read(file_path="<prd-source-dir>/brand-new-day-prd-v1.5.md", offset=1326, limit=44)
# → Reads Patches 1–4 only (lines 1326–1369)
```

## Task-Based Navigation

| Task | Read these lines |
|---|---|
| Understand what Phase 1.5 is and why it exists | 803–818 (§8 intro) |
| Understand Phase 1.5 full scope and sub-phases | 803–978 (§8 complete) |
| Work on security refactor (`.env`, `BND_HOME`) | 819–834 (§8.1) |
| Work on rubric externalization to `config.yml` | 835–870 (§8.2 incl. §8.2.0) |
| Work on permission-clean scan invocation | 837–853 (§8.2.0) |
| Work on GitHub repo setup and `.gitignore` | 871–888 (§8.3) |
| Work on `install.sh` or `init`/`doctor`/`reset` | 889–904 (§8.4) |
| Check what is explicitly out of scope for 1.5 | 905–920 (§8.5) |
| Verify security checklist before going public | 921–932 (§8.6) |
| Know what done looks like for Phase 1.5 | 933–943 (§8.7) |
| Check sequencing and session estimates | 966–978 (§8.10) |
| Understand scoring engine (dimensions, weights) | 317–403 (§6.2) |
| Work on the dashboard or review workflow | 404–507 (§6.3 + §7.3.3) |
| Understand what changed in v1.5 vs. v1.4 | 1292–1325 (Appendix E core) |
| Read post-sign-off patches (P1 through P4) | 1326–1369 (Appendix E tail) |
| Look up a specific decision (D-001 to D-016) | 1231–1257 (Appendix C) |
| Understand Phase 2 scope (what comes after 1.5) | 1036–1059 (§10 Phase 2 + Future) |
| Understand the full system architecture | 101–170 (§6 overview) |

## Section-by-Section Index

| Lines | Section | Summary |
|---|---|---|
| 1–13 | Header metadata | Version 1.5, signed 2026-04-16, patched 2026-04-22 + 2026-04-27 |
| 15–25 | §1 Executive Summary | What Brand New Day does; Phase 1 complete; v1.5 = GitHub alpha packaging |
| 27–49 | §2 Problem Statement | Daily 1–2hr triage grind; what stays manual (LinkedIn, Google Alerts, apply) |
| 51–68 | §3 Goals & Success Metrics | Four primary metrics (time, speed, SNR, missed matches); three secondary goals |
| 70–85 | §4 User Stories | 10 user stories spanning triage, scoring, review, dedup, and credit safety |
| 87–100 | §5 Design Principles | Five principles: no copy-paste, overnight credits, degrade gracefully, audit everything, flag what isn't automated |
| 101–170 | §6 System Architecture (overview) | ASCII flow diagram (Scheduler → Search → Enrichment → Scoring → Data → Dashboard) + 4 key design decisions |
| 173–262 | §6.1.1–6.1.2 (partial) | Search keywords config; JSearch (primary) and Adzuna (supplemental) source specs |
| 263–315 | §6.1.3–6.1.6 | Query construction; result processing; adding sources; future source discovery |
| 317–403 | §6.2 Scoring Engine | 10 dimensions with weights; composite formula; hard gate behavior; score output JSON; configurable scoring in config.yml |
| 404–507 | §6.3 + §7.3.3 | Dashboard format, sections, card contents, state filter tabs, below-threshold section, run log footer; review tracking (reviewed.json, localStorage sync) |
| 508–571 | §6.4 Data Layer | listings.json, scan-state.json, reviewed.json, and config.yml schemas |
| 572–650 | §6.5 Scheduling & Credit Management | Two execution modes; the user's credit schedule; operations budget; catch-up logic; run logging |
| 651–733 | §6.6 Configuration | Full default config.yml with keywords, sources, scoring weights, scheduling, output, and profile path |
| 734–772 | §7.1–7.2 Technical Design | Skill file structure; manual and scheduled invocation; Phase 1.5 subcommands (`init`, `doctor`, `reset`) |
| 773–802 | §7.3–7.5 | Dedup strategy (normalized hash); dashboard refresh (full regeneration each run); Playwright (installed, when it kicks in) |
| 803–818 | §8 Phase 1.5 Intro | Why public repo; why "technical folks" audience; scope framing (packaging only, not scanner changes) |
| 819–834 | §8.1 Sub-Phase 1.5a | Security + path portability: `.env`, `BND_HOME`, strip absolute paths, `.env.example`. 5 tasks + exit criteria. ✅ COMPLETE |
| 835–836 | §8.2 Sub-Phase 1.5b header | Section header; content split into §8.2.0 + §8.2.1 |
| 837–853 | §8.2.0 Replication-Ready Scan Invocation | Patched in 2026-04-22 (P1+P2). Stdlib helpers + native Read/Write/Edit + no-inline-python rule. ✅ COMPLETE |
| 854–870 | §8.2.1 Rubric & Profile Externalization | 6 tasks moving the user-specific calibration into `config.yml` + `profile.md`. ✅ COMPLETE |
| 871–888 | §8.3 Sub-Phase 1.5c | Repo packaging: GitHub repo, layout, `.gitignore`, pre-commit hook, README, security warning, dashboard template. 7 tasks + exit criteria. ✅ COMPLETE 2026-04-27 |
| 889–904 | §8.4 Sub-Phase 1.5d | Install + onboarding: `install.sh`, `/brand-new-day init` validator, `doctor`, cron setup docs, `reset`. 5 tasks + exit criteria. ✅ COMPLETE 2026-04-27 |
| 905–920 | §8.5 Out of Scope | Explicit deferrals: Adzuna, multi-source abstraction, non-PM rubrics, Windows/Linux, GUI, interview-prep handoff, cover letter, feedback loop, Notion push |
| 921–932 | §8.6 Security Safeguards | Five non-negotiable pre-public checks: secrets in history, personal data in history, gitignore dry-run, pre-commit hook, README warning |
| 933–943 | §8.7 Success Metrics | Four Phase 1.5 success criteria: no regression, 15-min install, zero-leak public push, config-only role change |
| 944–956 | §8.8 Risks | Six Phase 1.5 risks with likelihood and mitigation |
| 957–965 | §8.9 Resolved Decisions | Four settled decisions: repo name, sources in alpha (JSearch only), cron setup (manual/README only), example listings (none) |
| 966–978 | §8.10 Sequencing & Estimates | Sub-phase estimates: 1.5a (1 session), 1.5b (1–2), 1.5c (1), 1.5d (1–2). Total: 4–6 sessions. Actuals: ~7 sessions across multiple days |
| 979–1009 | §9 Integration Points | Interview-prep handoff (data-layer-based, zero copy-paste); cover letter generation (Phase 2); Notion push (Future) |
| 1010–1035 | §10 Phases — Phase 1 & 1.5 tables | Phase 1 components all marked ✅ COMPLETE; Phase 1.5 four deliverables mapped to sub-phases |
| 1036–1059 | §10 Phases — Phase 2 & Future | Phase 2 features (interview-prep handoff, ATS APIs, cover letter, feedback loop, more sources); Future (LinkedIn, Google Alerts, auto-cover-letter, analytics, mobile) |
| 1060–1076 | §10.1 Build Estimate | Phase 1 actuals vs. estimates; pivot cost noted |
| 1077–1101 | §11 Constraints & Risks | Five constraints ($20 plan, no LinkedIn, no auto-apply, local-only, rate limits); six risks with likelihood/impact/mitigation |
| 1102–1152 | §11.1 Credit Observability | Per-run tracking (run-log.json); project-level credit ledger (credit-ledger.json schema and activity types) |
| 1153–1167 | §12 Glossary | 8 terms: ATS, hard gate, operations budget, composite score, catch-up, PLG, DXP, BND_HOME |
| 1168–1195 | Appendix A | the user's profile summary — strongest/good/weak match signals for scoring calibration |
| 1196–1230 | Appendix B | Lineage: santifer/career-ops, Masterjx9/OpenPostings, JSearch, Adzuna, dead ends |
| 1231–1257 | Appendix C | Decision log D-001 through D-016. D-014–D-016 are Phase 1.5 decisions |
| 1258–1291 | Appendix D | v1.3→v1.4 changelog: JSearch pivot, cron disabled, decisions D-011–D-013 |
| 1292–1325 | Appendix E (core) | v1.4→v1.5 changelog: what was added (§8, D-014–D-016), updated, and unchanged |
| 1326–1329 | Appendix E — Patch 1 | 2026-04-22 — added §8.2.0 (replication-ready scan invocation, JSearch call) |
| 1330–1333 | Appendix E — Patch 2 | 2026-04-22 — extended §8.2.0 (helpers + native tools for full scan flow) |
| 1334–1349 | Appendix E — Patch 3 | 2026-04-27 — Phase 1.5c shipped (public repo) + pre-commit hook hardening |
| 1350–1369 | Appendix E — Patch 4 | 2026-04-27 — Phase 1.5d shipped (install.sh + init/doctor/reset). Phase 1.5 complete |

## v1.4 → v1.5 Delta (Quick Reference)

**What's new in v1.5** (if coming from a v1.4 session):

| What | Where |
|---|---|
| Section 8 — Phase 1.5 in full (§8.1–8.10) | Lines 803–978 |
| Phase 1.5 subcommands in §7.2 (`init`, `doctor`, `reset`) | Lines 754–772 |
| Phase 1.5 column in §10 roadmap table | Lines 1027–1035 |
| Phase 1 actuals in §10.1 | Lines 1060–1076 |
| `BND_HOME` in §12 Glossary | Line 1166 (within 1153–1167) |
| Decisions D-014, D-015, D-016 in Appendix C | Within 1231–1257 |
| Appendix E (changelog + patches) | Lines 1292–1369 |

**All Phase 1 content is unchanged.** §1–§7, §9, §11–§12, Appendix A–D are verbatim from v1.4.

## Patches Reference

Four patches have been applied since v1.5 was signed off on 2026-04-16. All live in Appendix E (lines 1326–1369). Read these to catch up on what changed post-sign-off:

| Patch | Date | What | Lines |
|---|---|---|---|
| P1 | 2026-04-22 | Added §8.2.0 (replication-ready scan invocation, JSearch call) | 1326–1329 |
| P2 | 2026-04-22 | Extended §8.2.0 (helpers + native tools for full scan flow) | 1330–1333 |
| P3 | 2026-04-27 | Phase 1.5c shipped (public repo) + pre-commit hook hardening | 1334–1349 |
| P4 | 2026-04-27 | Phase 1.5d shipped (install.sh + init/doctor/reset). Phase 1.5 COMPLETE | 1350–1369 |

## Section Numbering Notes

v1.5 inherits v1.4's numbering inconsistencies: §7.3.3 (Review Tracking) appears inside §6.3, and §7.5.1 appears inside §6.5. These are in the signed-off document and should not be "fixed" — just be aware when citing sections. The new §8 (Phase 1.5) uses clean sub-numbering (§8.1–§8.10), with §8.2 split into §8.2.0 (patched in) and §8.2.1.

## Maintenance Note

This guide's line ranges drift every time the PRD is patched. If you add a patch or new section to v1.5, refresh this guide by running `grep -nE "^(#|##|###|####) " brand-new-day-prd-v1.5.md` and recomputing the ranges. A future improvement would be a tiny script that auto-regenerates the section index from the actual headers.
