---
name: vibe-checkup
description: Run a health checkup on an AI-iterated (vibe coding) project to find buildup that will mislead the next agent (duplicate implementations, hardcoded values, stale docs, missing rules, bloated tests, releases with no rollback, etc.). Produces an evidence-backed severity report, ready-to-paste agent rules, and remediation tasks. Use when the user asks for a checkup, health check, project audit, or codebase governance; says the project is getting messier, adding features is getting harder, or AI-written code is out of control; or before starting a major feature or shipping a release on an AI-built project.
---

# Vibe Checkup

An AI-iterated project does not break overnight—it accumulates **sediment**. Every iteration leaves behind another layer of uncleaned styles, fallbacks, design proposals, and tests until adding new features becomes a slog. A checkup answers one question:

> **What in this repo will cause the next agent to write worse code, or make it harder for humans to verify and maintain?**

Every finding must explain how it misleads the next agent (or harms users). If you cannot explain that, it is not a finding.

## Before You Start

1. **Read `references/agent-brief.md` first**: discipline, finding format, and severity rules. Both the main agent and every sub-agent follow it. The most important rule is **diagnose only—do not operate**: the only write allowed is `<project>/.vibe-checkup/`; running tests, launching the app, network access, and compiling all require asking the user first.
2. **Choose the mode**: normal mode is the default and is described below. If the user says "quick / rough / quick pass / incremental check" → use fast mode (check only ★ items; when a baseline exists, inspect only changes since the baseline), and read `references/fast-mode.md`, which details every step that differs from below.
3. Scripts require Python 3 (use `python3` if `python` is unavailable). If neither exists, tell the user and stop.

## Model Allocation

Sub-agents inherit the main session's model by default, which wastes the most expensive model on mechanical code reading. Split work into two tiers:

- **Top tier** (main session model, no override): Step 1 profiling (getting the project stage wrong throws off severities across every dimension), Dimension 3 (3.2 is the most likely place to produce 🔴), Step 3 verification, and Step 4 scoring and report writing.
- **Standard tier** (one tier below the main session model in your environment): Dimensions 1, 2, 4, 5, and 6; Step 5 execution after user approval (the main agent must still inspect the diff personally).

Specify the tier using your environment's mechanism—for example, pass `model: "sonnet"` to Claude Code's Agent tool, or use the mid-tier model / lower reasoning effort in other environments. If you cannot specify a model, inherit it; never skip check items to save tokens.

## Workflow

### 1. Project Profiling

1. Run `python <skill_dir>/scripts/baseline.py stamp <project_root>` to obtain `commit` and `dirty`, and to create `.vibe-checkup/` with its `.gitignore`. If the output contains `git_error:` (exit code 2): stop, show the raw error to the user (commonly Windows `dubious ownership`), and wait until it is fixed before continuing. **Do not** treat this as "not a git repository".
2. Run the mechanical scan and save output to a temp directory—never write it into the project. Main-agent profiling only needs §0 (Profile), §5 (Docs & rules), and §7 (Git history), so fetch only those three sections:
   `python <skill_dir>/scripts/scan.py <project_root> --section 0,5,7 > <temp_dir>/scan.md`
   Handle `GIT ERROR` in `scan.md` §0 the same way as above. Each sub-agent fetches its own sections in Step 2; if running sequentially without sub-agents, fetch each dimension's sections only when you reach that dimension.
3. Read `scan.md`, README, all agent rule files, dependency manifests, a two-level directory tree, and `git log --oneline -30`. If `<project>/.vibe-checkup/report.md` exists (the previous normal checkup), read it too.
4. Write a **profile card** to `<temp_dir>/card.md` (sub-agents read it directly so you do not have to repeat it in every prompt) with these fixed fields:
   - One-sentence project summary; tech stack
   - Stage: `prototype` / `personal` / `pre-release` / `released`, with rationale; distribution method
   - Has UI (yes/no)
   - 3–5 core user flows, each written as "entry point → result the user gets"
   - Key locations: where tokens/themes, shared components, utility functions, docs, tests, and rule files live (write "none" if absent). List **git-ignored docs that rule files tell agents to read** (scan §5 "ignored docs referenced by rule files") separately—Dimension 3 must inspect them
   - Directories to exclude from review (other branch worktrees, generated artifacts, third-party code, private data)
   - Applicable and non-applicable dimensions (with reasons); if the user specified a scope, list only those
   - Path to `scan.md`
5. **Confirm the stage**: in 1–2 sentences, tell the user the inferred stage, distribution method, and excluded directories. If the evidence is insufficient (cannot tell whether there are external users, whether it is commercial, or whether a directory is third-party code), **ask the user once** before proceeding—a wrong stage invalidates every downstream severity. If the evidence is clear, continue without waiting for a reply.

Completion criteria: every field on the profile card is filled in, and the stage has clear evidence.

### 2. Per-Dimension Checks

| # | Dimension | Reference File | scan Sections | Applicability |
|---|-----------|----------------|---------------|---------------|
| 1 | Consistency & Single Source of Truth (style tokens, shared components, interaction patterns, architectural patterns) | `references/01-consistency.md` | 0,2 | All items if UI exists; 1.7 only if no UI |
| 2 | Code Hygiene (hardcoding, duplicate implementations, fallback stacking, mock/placeholder data, swallowed errors, type escapes, god files, one-off scripts, lying comments) | `references/02-code-hygiene.md` | 0,1,2,4 | Always |
| 3 | Docs & Rules (doc rot, proposal quality, rule file quality, duplicated rules) | `references/03-docs-and-rules.md` | 0,4,5,7 | Always |
| 4 | Test Suite (layering, superficial tests, critical paths, manual acceptance, programmatic debug tools) | `references/04-tests.md` | 0,6 | Always |
| 5 | Dependencies, Licenses & Security | `references/05-deps-and-security.md` | 0,3,7,8 | Always |
| 6 | Delivery & Iteration Governance (git, branching, release gates, rollback, safe mode, bug-churn stop-loss, fresh-env setup) | `references/06-delivery-and-iteration.md` | 0,7 | Always; release items (6.3–6.6) apply only to `pre-release` and `released`—mark N/A for other stages |

- **When sub-agents are available**, dispatch them in parallel using the tiers from "Model Allocation":
  - Fewer than 5,000 source lines (scan §0 `source lines`): dispatch three sub-agents. A = Dimensions 1+2 (Standard tier), B = Dimension 3 (Top tier), C = Dimensions 4+5+6 (Standard tier); take the union of their scan sections. On small projects, per-agent ramp-up overhead exceeds the inspection itself.
  - Otherwise, dispatch one sub-agent per applicable dimension.
  - Shared rules and formats live in the brief—do not repeat them in prompts. Each sub-agent prompt should contain only:
    - Instruction to read `<skill_dir>/references/agent-brief.md` and `<temp_dir>/card.md` first
    - Its assigned dimension(s) and reference file path(s)
    - Its scan command: `python <skill_dir>/scripts/scan.py <project_root> --section <sections from table>`
    - Its findings file path: `<temp_dir>/findings-<dim>.md` (shared file when one agent covers multiple dimensions, e.g. `findings-1-2.md`)
- **When sub-agents are unavailable**: work through dimensions one by one, reading each reference file and fetching its scan sections only when you reach it; after finishing each dimension, write its findings to its findings file in the brief's format.

**Write findings once**: full findings live only in the findings files. Sub-agents return only one-line summaries per finding plus the score sheet; the main agent never re-types findings—Step 4 assembles the "All Findings" section directly from the findings files via script.

Completion criteria: **every check item** in every applicable dimension has a verdict—`finding` / `pass` / `N/A (<one-line reason>)` / `needs approval, not run`. Missing even one item means the step is incomplete.

### 3. Verification & Synthesis

1. **Verify** every 🔴 and 🟠 finding: read the full entry in the findings file, re-open the cited code (default to ±30 lines around `path:line`, expanding only if context is needed; read across files as needed for duplication or architecture findings), and **try to disprove it**—is it third-party or generated code? Is there a documented legitimate reason? Does this path actually execute? Is it already guarded elsewhere? If it holds up, verify its confidence (`High` / `Medium` / `Low`); if disproven, downgrade or delete it. Whenever a verdict changes, update both that entry in the findings file and its line in the score sheet directly. Also spot-check 1–2 ★ items marked `pass` by Standard-tier sub-agents (verification catches false positives, not false negatives).
2. **Cross-verification**: when a second model is callable in your environment (e.g., Codex CLI or a delegation skill), hand the 🔴 findings and evidence paths to it for independent review (read-only mode; give only the question and paths, never your verdict). If opinions conflict, mark the finding `disputed`: **score by majority** (inspector, main-agent verifier, and second model; with only two parties, follow the main-agent verifier), record each view in the report, and add it to "Decisions Needed".
3. **Deduplicate**: when two dimensions report the same root cause (for example, two HTTP libraries flagged under both 1.7 and 5.4), keep it under the single best-fitting check item; remove the duplicate from the other findings file and write `1.7 see 5.4` in the score sheet.
4. **Identify cross-dimension recurring patterns**: list issue categories appearing in two or more places across dimensions and check them against the rule files (from 3.3) to see whether any rule prevents them. This feeds "Suggested Rules" in Step 5.

Completion criteria: every 🔴/🟠 finding carries a confidence level and has survived a disproval attempt; no root cause is double-scored.

### 4. Scoring & Reporting

**Delegate scoring to the script—never calculate by hand**:
1. Save the verified score sheet to `<project>/.vibe-checkup/scores.txt` (overwriting the previous file; read the old one first for comparison). One check item per line: `1.1 🟠` (highest severity finding for that item) / `1.2 pass` / `1.5 N/A (no UI)` / `5.4 needs approval, not run` / `1.7 see 5.4`.
2. Run `python <skill_dir>/scripts/baseline.py score <project>/.vibe-checkup/scores.txt` to get per-dimension scores, total score, and health grade.

Script formula (for explaining scores to the user): each check item is deducted once based on its highest-severity finding—🔴 −4, 🟠 −2, 🟡 −1, ⚪ 0—so merging or splitting findings does not distort the score; dimension score = `10 × max(0, 1 − deduction / (2 × scored_items))`, where only `finding` and `pass` count as scored; total score = average of scored dimension scores × 10; grades: 85+ `Healthy`, 70–84 `Fair`, 50–69 `Needs Remediation`, <50 `Out of Control`, **capped at `Needs Remediation` whenever any 🔴 exists**.

Comparison with the previous checkup: compare total scores only when both runs have the **exact same set of scored dimensions**; otherwise compare only per-dimension scores and specific findings.

**Report**:
- Follow `references/report-template.md` and save to `<project>/.vibe-checkup/report.md`, **overwriting** the previous file—checkup reports themselves must not become sediment. If a prior report exists, write the comparison into the new report before overwriting.
- In the "All Findings" section, write only a single `<!-- FINDINGS -->` line. After writing the report, run `python <skill_dir>/scripts/baseline.py assemble <report_path> <findings_file...>` (list findings files in dimension order) to replace the placeholder with the full findings.
- This report also serves as the **baseline** for fast mode: put `mode: normal`, date, `commit`, and `dirty` in front matter (copy the last two verbatim from Step 1's `baseline.py stamp` output), and keep the complete profile card in the body. `scores.txt` is also part of the baseline.
- In chat, give the user: total score and grade, the top 3–5 items to tackle first, and the report path.

### 5. Prescription (Propose Only—Do Not Execute)

End the report with three sections, then ask the user which items to tackle first:

1. **Stop the Bleeding**: all 🔴 findings—one line each with title and minimal fix (full text lives in "All Findings"; do not repeat it).
2. **Suggested Rules** (rule codification): turn the unguarded recurring patterns from Step 3 into rules ready to paste into `AGENTS.md` / `review.md`—one rule per line, stated affirmatively, pointing to the single source of truth. Fixing code without adding a rule guarantees the next agent will repeat the mistake.
3. **Remediation Tasks**: group remaining findings into independent tasks, each sized for a single agent session and paired with acceptance criteria.

Act only after the user approves. During execution: present a deletion list to the user before deleting anything; commit changes per task; run only module-scoped tests after each edit, then run the full test suite once all feature-level changes are complete. **When edits touch files without test coverage** (entry points, main window processes, startup scripts), green tests do not prove the app runs: at minimum run the "Name resolution" check from `references/04-tests.md` 4.4 on the modified files, and list "manual startup verification points" in the handoff note. When delegating execution to a sub-agent, the main agent must inspect the diff personally rather than relying solely on its summary.
