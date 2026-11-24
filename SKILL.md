---
name: vibe-checkup
description: Run a health checkup on an AI-iterated (vibe coding) project to find buildup that will mislead the next agent (duplicate implementations, hardcoded values, stale docs, missing rules, bloated tests, releases with no rollback, etc.). Produces an evidence-backed severity report, ready-to-paste agent rules, and remediation tasks. Use when the user asks for a checkup, health check, project audit, or codebase governance; says the project is getting messier, adding features is getting harder, or AI-written code is out of control; or before starting a major feature or shipping a release on an AI-built project.
---

# Vibe Checkup

A checkup answers one question:

> **What in this repo will cause the next agent to write worse code, or make it harder for humans to verify and maintain?**

Every finding must explain how it misleads the next agent (or harms users). If you cannot explain that, it is not a finding.

## Before You Start

1. **Read `references/agent-brief.md` first**: discipline, finding format, and severity rules (followed by both main agent and sub-agents). **Diagnose only**: the only permitted write is `<project>/.vibe-checkup/`; ask the user before running tests, launching the app, network access, or compiling.
2. **Treat `scripts/` as black boxes**: invoke `scripts/scan.py` and `scripts/baseline.py` via CLI (`--help` for flags). Do **not** read their source code into context. Requires Python 3 (`python3` if `python` is unavailable); if neither exists, tell the user and stop.
3. **Choose mode**: normal mode is default (below). If the user asks for a quick / rough / incremental check → use fast mode and read `references/fast-mode.md` (checks ★ items only; incremental scope when a baseline exists).

## Model Allocation

- **Top tier** (main session model, no override): Step 1 profiling, Dimension 3, Step 3 verification, Step 4 scoring & report writing.
- **Standard tier** (one tier below main session model): Dimensions 1, 2, 4, 5, 6; Step 5 execution after user approval (main agent must still inspect the diff personally).

Specify the tier via your environment's mechanism (e.g., `model: "sonnet"` for Claude Code's Agent tool, or mid-tier / lower reasoning effort elsewhere). If unsupported, inherit; never skip check items to save tokens.

## Workflow

### 1. Project Profiling

1. Stamp baseline and initialize `<project>/.vibe-checkup/` (with its own `.gitignore`):
   ```bash
   python <skill_dir>/scripts/baseline.py stamp <project_root>
   ```
   Returns `commit` and `dirty`. On `git_error:` (exit code 2, commonly Windows `dubious ownership`): stop, show the raw error, and wait until fixed—**do not** treat as "not a git repository".

2. Run the mechanical scan to a temp directory (never inside the project), fetching only §0, §5, §7 for profiling:
   ```bash
   python <skill_dir>/scripts/scan.py <project_root> --section 0,5,7 > <temp_dir>/scan.md
   ```
   Handle `GIT ERROR` in §0 the same way. Sub-agents fetch their own sections in Step 2 (if sequential, fetch per dimension when reached).

3. Read `scan.md`, README, all agent rule files, dependency manifests, a two-level directory tree, `git log --oneline -30`, and `<project>/.vibe-checkup/report.md` (if present).

4. Write `<temp_dir>/card.md` with these fixed fields:
   - One-sentence project summary; tech stack
   - Stage (`prototype` / `personal` / `pre-release` / `released`) with rationale; distribution method
   - Has UI (`yes` / `no`)
   - 3–5 core user flows (`entry point → result the user gets`)
   - Key locations: tokens/themes, shared components, utilities, docs, tests, rule files (`none` if absent). List **git-ignored docs referenced by rule files** (scan §5) separately for Dimension 3
   - Excluded directories (other branch worktrees, generated artifacts, third-party code, private data)
   - Applicable and non-applicable dimensions (with reasons; honor user-specified scope)
   - Path to `scan.md`

5. **Confirm stage**: in 1–2 sentences, report inferred stage, distribution method, and excluded directories. Ask the user **once** before proceeding only if evidence is insufficient (unclear whether external users exist, commercial intent, or third-party dirs); otherwise continue without waiting.

**Completion criteria**: every profile card field is filled and stage has clear evidence.

### 2. Per-Dimension Checks

| # | Dimension | Reference File | scan Sections | Applicability |
|---|-----------|----------------|---------------|---------------|
| 1 | Consistency & Single Source of Truth | `references/01-consistency.md` | 0,2 | All if UI exists; 1.7 only if no UI |
| 2 | Code Hygiene | `references/02-code-hygiene.md` | 0,1,2,4 | Always |
| 3 | Docs & Rules | `references/03-docs-and-rules.md` | 0,4,5,7 | Always |
| 4 | Test Suite | `references/04-tests.md` | 0,6 | Always |
| 5 | Dependencies, Licenses & Security | `references/05-deps-and-security.md` | 0,3,7,8 | Always |
| 6 | Delivery & Iteration Governance | `references/06-delivery-and-iteration.md` | 0,7 | Always; 6.3–6.6 apply only to `pre-release` / `released` (`N/A` otherwise) |

- **With sub-agents** (parallel, using tiers from Model Allocation):
  - `< 5,000` source lines (scan §0 `source lines`): dispatch 3 sub-agents — **A** = Dim 1+2 (Standard), **B** = Dim 3 (Top), **C** = Dim 4+5+6 (Standard); union their scan sections.
  - Otherwise: dispatch 1 sub-agent per applicable dimension.
  - Keep prompts minimal (do not repeat rules from `agent-brief.md`):
    - Read `<skill_dir>/references/agent-brief.md` and `<temp_dir>/card.md` first
    - Assigned dimension(s) and reference file path(s)
    - Scan command: `python <skill_dir>/scripts/scan.py <project_root> --section <sections>`
    - Output findings file: `<temp_dir>/findings-<dim>.md` (e.g., `findings-1-2.md` when grouped)
- **Without sub-agents**: run dimensions sequentially, reading each reference and fetching its scan sections only when reached; write each findings file in the brief's format.
- **Write findings once**: full findings live only in `<temp_dir>/findings-*.md`; sub-agents return one-line summaries + score sheet; Step 4 splices findings files via script.

**Completion criteria**: every check item in every applicable dimension has a verdict (`finding` / `pass` / `N/A (<reason>)` / `needs approval, not run`).

### 3. Verification & Synthesis

1. **Verify every 🔴 and 🟠**:
   - Read the full entry in its findings file and re-open cited code (±30 lines around `path:line`, expanding or checking across files as needed).
   - Try to disprove: third-party or generated? documented legitimate reason? unreachable path? already guarded elsewhere?
   - If it holds, confirm `Confidence` (`High` / `Medium` / `Low`); if disproven, downgrade or delete and update both the findings file and score sheet directly.
   - Spot-check 1–2 ★ items marked `pass` by Standard-tier sub-agents.
2. **Cross-verify 🔴** (when a second model is callable, e.g., Codex CLI or delegation skill):
   - Pass only the question and evidence paths in read-only mode—never your verdict.
   - On conflict, mark `disputed`, **score by majority** (inspector, verifier, second model; with 2 parties, follow main-agent verifier), record each view in the report, and add to "Decisions Needed".
3. **Deduplicate**: when two dimensions flag the same root cause (e.g., duplicate HTTP libraries in 1.7 and 5.4), keep it under the single best-fitting item, remove from the other findings file, and write `1.7 see 5.4` in the score sheet.
4. **Cross-dimension patterns**: list issue categories appearing in ≥2 places across dimensions and check against rule files (from 3.3) to feed "Suggested Rules".

**Completion criteria**: every 🔴/🟠 finding carries a confidence level and survived disproval; no root cause is double-scored.

### 4. Scoring & Reporting

**Delegate scoring to the script—never calculate by hand**:

1. Read prior `<project>/.vibe-checkup/scores.txt` (if any) for comparison, then overwrite it with the verified score sheet (one item per line: `1.1 🟠` / `1.2 pass` / `1.5 N/A (no UI)` / `5.4 needs approval, not run` / `1.7 see 5.4`).
2. Score via script:
   ```bash
   python <skill_dir>/scripts/baseline.py score <project>/.vibe-checkup/scores.txt
   ```
   - For explaining scores: each item deducts once by its highest severity (🔴 > 🟠 > 🟡, ⚪ = 0); grades are 85+ `Healthy`, 70–84 `Fair`, 50–69 `Needs Remediation`, <50 `Out of Control`, **capped at `Needs Remediation` whenever any 🔴 exists**.
   - Compare total scores with the previous checkup only when both runs have the **exact same set of scored dimensions**; otherwise compare only per-dimension scores and specific findings.

**Report**:

- Follow `references/report-template.md` and overwrite `<project>/.vibe-checkup/report.md` (read the prior report first to write the comparison).
- In "All Findings", write only a single `<!-- FINDINGS -->` line, then splice findings files in dimension order:
  ```bash
  python <skill_dir>/scripts/baseline.py assemble <report_path> <findings_file...>
  ```
- Baseline fields: set `mode: normal`, `date`, `commit`, and `dirty` in front matter (copy `commit` and `dirty` verbatim from `baseline.py stamp`) and include the full profile card in the body. `scores.txt` is also part of the baseline.
- In chat, output: total score & grade, top 3–5 priority items, and report path.

### 5. Prescription (Propose Only—Do Not Execute)

End the report with three sections, then ask the user which items to tackle first:

1. **Stop the Bleeding**: all 🔴 findings—one line each (title + minimal fix; do not duplicate full text from "All Findings").
2. **Suggested Rules**: unguarded recurring patterns from Step 3, ready to paste into `AGENTS.md` / `review.md`—one affirmative rule per line pointing to the single source of truth.
3. **Remediation Tasks**: remaining findings grouped into single-session tasks with acceptance criteria.

**After user approval (execution rules)**:

- Present a deletion list before deleting anything.
- Commit per task; run module-scoped tests after each edit, then the full test suite once feature-level changes finish.
- When editing files without test coverage (entry points, main window processes, startup scripts): run the "Name resolution" check from `references/04-tests.md` 4.4 on modified files and list manual startup verification points in the handoff note.
- When delegating execution to a sub-agent, inspect the diff personally rather than relying on its summary.
