# Report Template

This report is written for the project author, who may not know the implementation language. Lead every section with the conclusion, then give evidence; keep technical details inside individual finding entries rather than the overall assessment. Write "None" for empty sections—never delete sections. Redact all secrets.

Front matter is machine-parsed—do not rename keys. Normal mode writes `report.md`; fast mode writes `fast-report.md`:

````markdown
---
mode: normal            # write "fast" for fast mode
date: YYYY-MM-DD
commit: <full hash at profiling time; write "none" if not a git repo>
dirty: false            # whether the working tree had uncommitted changes at profiling time
# Add these three lines in fast mode only:
# base: <baseline commit; write "none" if no baseline>
# head: <commit at this profiling run>
# scope: <incremental: N files changed | full: no baseline (no record / commit missing / changes too large)>
---

# Project Checkup Report: <project_name>

- Date: YYYY-MM-DD
- Stage: prototype / personal / pre-release / released (basis: …); distribution: installer/binary / hosted service / run from source
- Tech stack: …
- Checkup mode: normal / fast (fast mode checks ★ items only; state review scope); cross-verified by a second model: yes / no
- Not run (requires approval): … (e.g., running tests, launching the app, online audit)
- Scored dimensions: 1, 2, 3, 4, 5, 6 (list reasons for any N/A dimensions)

## Project Profile

(Copy all fields from Step 1's profile card; fast mode reuses this, so normal mode must fill it in completely.)

## Overall Assessment

**<total>/100 · <Healthy | Fair | Needs Remediation | Out of Control>**
(Capped at "Needs Remediation" whenever any 🔴 exists.)

<2–3 sentence diagnosis: where the project's primary sediment sits, and what will break first if left unaddressed.>

| Dimension | Score | 🔴 | 🟠 | 🟡 | ⚪ | One-liner |
|-----------|-------|----|----|----|----|-----------|
| 1 Consistency & Single Source of Truth | x/10 | | | | | |
| 2 Code Hygiene | | | | | | |
| 3 Docs & Rules | | | | | | |
| 4 Test Suite | | | | | | |
| 5 Dependencies, Licenses & Security | | | | | | |
| 6 Delivery & Iteration Governance | | | | | | |

(Scored per check item: each item is deducted once by its highest-severity finding, with 🔴 deducting the most; each dimension is out of 10.)

### Comparison with Previous Checkup
(Write "First checkup" if no previous report exists.)
- Total score: previous → current (write "Scope differs; total scores not comparable" when scoring rules disallow comparison; in fast mode with no baseline, write "No baseline for comparison")
- Dimension scores: previous → current
- Resolved: …
- Newly introduced: …
- **Recurring** (present last time and still unresolved): … ← prime candidates for rules or hard gates

## Stop the Bleeding (🔴)

One line per finding: title (check item ID) + minimal fix; full details live in "All Findings"—do not duplicate them here. For disputed findings, state each party's view (inspector / main-agent verifier / second model) and the scoring basis.

## All Findings

<!-- FINDINGS -->

(Keep the line above verbatim and do not write findings yourself: `baseline.py assemble` replaces it with the full contents of the findings files. Do not include this note in the final report.)

## Suggested Rules

Distilled from the unguarded recurring patterns found in Step 3. One rule per line, stated affirmatively, pointing to the single source of truth, and citing the source finding ID.

```md
<!-- Suggested additions to AGENTS.md (or CLAUDE.md) -->
- Colors, spacing, and border radii must come from `<token file path>`; add new values to the token file first. (From 1.1)
- Use `<ComponentName>` for small-set single-choice inputs instead of dropdowns. (From 1.3)
- When modifying a single module, run only `<scoped test command>`; save the full test suite for after the feature is complete. (From 4.2)
```

```md
<!-- Suggested additions to review.md / review checklist -->
- …
```

## Remediation Tasks

Each task should be self-contained and sized for a single agent session.

| # | Task | Findings Resolved | Effort | Acceptance Criteria | Prerequisite |
|---|------|-------------------|--------|---------------------|--------------|
| 1 | | | S/M/L | Verifiable completion condition | |

## Decisions Needed

Decisions only the project author can make: cutting or rethinking a stuck feature (6.8), license resolution (5.5), confirming the stage assessment, whether to run tests or launch the app for live checks (4.1, 1.5), whether a proposed rule matches product intent… List options and trade-offs for each.

## Check Coverage

| Dimension | Findings | Pass | N/A | Needs Approval, Not Run | Not Checked (Fast Mode) | Carried from Baseline (Fast Mode) |
|-----------|----------|------|-----|-------------------------|-------------------------|-----------------------------------|
| 1 | 1.1, 1.3 | 1.2, 1.4 … | 1.5 (no UI) | | | |
| … | | | | | | |

Summarize passing items concisely in one line so the author knows what was checked and is healthy. List items merged into another check item under "Findings" as `1.2 (see 1.1)`; they are not scored.
````
