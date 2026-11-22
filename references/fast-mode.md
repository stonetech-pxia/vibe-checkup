# Fast Mode

Use when the user says "quick / rough / quick pass / incremental check". The workflow still follows the five steps in `SKILL.md`; this file covers only what differs at each step.

- **Check items**: check only ★-marked items; mark all others `not checked (fast mode)`.
- **Review scope**: when a valid baseline exists, inspect only changes since the baseline commit; otherwise inspect the whole project. Baseline = `.vibe-checkup/report.md` from the most recent normal checkup.
- **Output files**: write `.vibe-checkup/fast-report.md` and `fast-scores.txt`, leaving `report.md` and `scores.txt` untouched—the baseline is always the latest normal checkup.

## Step 1: Determine Scope & Reuse Profile Card

After `baseline.py stamp`, run `python <skill_dir>/scripts/baseline.py scope <project_root>`. After reading the baseline's profile card, if it lists excluded directories, re-run with `--exclude <dir>` (repeatable). Check `verdict` in the output:

- `empty`: no changes since the baseline. Do not dispatch any sub-agents; mark all check items `carried from baseline` and note "No changes since baseline" in the report.
- `incremental`: **incremental scope = files listed under `changed:`** (`A` added / `M` modified / `D` deleted / `?` untracked).
- `full`: **no usable baseline**; `reason` explains why (no report / not a normal-mode report / commit hash no longer exists / changes exceed 40% of tracked files). Scope is the whole project (still ★ items only); run full profiling per `SKILL.md` Step 1. Explain the reason in chat and suggest running a normal checkup first to create or refresh the baseline.
- Exit code 2 or `git_error:`: git itself failed; handle as in `SKILL.md` Step 1.

40% is the default threshold and can be adjusted with `--threshold`. A baseline with `dirty: true` means it audited code that included uncommitted changes; because incremental scope compares the working tree against the baseline commit, those files are treated as changed and re-checked—erring on the side of over-inclusion.

**When a baseline exists**, skip full profiling: reuse the profile card from the baseline report, updating only fields affected by the changes, and save it to `<temp_dir>/card.md`. Read only the lines of `scan.md` relevant to the change set, any README / rule files / manifests in the change set, and `git log --oneline <baseline_commit>..HEAD`. Keep the baseline stage and tell the user in chat "Stage carried from baseline: X — let me know if this has changed" without waiting for confirmation.

## Step 2: Dispatch

- Change set has ≤ 10 files: do not dispatch sub-agents; the main agent runs the checks directly (still writing findings to findings files).
- Otherwise, regardless of project size, use the three-group split from `SKILL.md` Step 2 (A / B / C). When there is no baseline (whole-project scope), still use those three groups.
- When a baseline exists, pass `--since <baseline_commit>` to `scan.py`.
- In addition to the normal-mode prompt, give each sub-agent: the path to this file (instructing it to read "Incremental Scope Review Rules"), "★ items only", the change-set list (or "no baseline"), and any baseline findings relevant to its dimension(s).
- Two extra verdicts apply: `not checked (fast mode)` and `carried from baseline`. In the score sheet, `carried from baseline` items must carry the baseline's verdict (copied from baseline `scores.txt`), written as `5.4 🟡 carried from baseline` or `5.4 pass carried from baseline`, so they are scored properly; omit non-★ items from the score sheet.

## Incremental Scope Review Rules (Sub-Agents Read This Section Too)

- Pass `--since <baseline_commit>` to `scan.py`: §1–§3 list only changed files, and §2 pattern hits are further filtered to **changed lines** (untracked new files count in full); §0 and §4–§8 remain whole-project facts. Note: renaming a symbol can break unchanged call sites that line-level filtering will not show—grep callers for renamed/changed symbols when needed.
- Inspect files and changed lines in the change set. You may read files outside the scope for comparison (e.g., repo-wide grep for duplicate implementations, checking token files), but **do not report pre-existing issues in unchanged files**—those belong to the baseline.
- For each baseline finding: if none of its evidence files are in the change set → `carried from baseline`, do not re-check; if any evidence file is in the change set → re-verify and note `still present` / `fixed` / `worsened`.
- Check items unrelated to the changes (e.g., manifests were untouched, so skip re-checking 5.4 and 5.5) → `carried from baseline`.
- Exception for 3.2: if code behavior changed, reverse-check docs and rule files referencing those paths or behaviors to see whether they went stale, even if the docs themselves were not edited.
- Under 4.4, also run the "Name resolution" check on the incremental scope (see `04-tests.md`).

## Step 3: Verification

Run the usual disproval attempt on every 🔴/🟠 finding; skip second-model cross-verification.

## Step 4: Scoring, Comparison & Report

- Save the score sheet to `.vibe-checkup/fast-scores.txt` (★ items only) and score it with `baseline.py score`. Scores are broadly comparable to normal mode; still note the mode in the report.
- `carried from baseline` items are scored using their baseline verdicts, so the incremental score reflects "baseline verdicts + new verdicts from this change set".
- Comparison: compare against the **same set of ★ items** in the baseline by running `python <skill_dir>/scripts/baseline.py score <project>/.vibe-checkup/scores.txt --items-from <project>/.vibe-checkup/fast-scores.txt`. If the baseline lacks `scores.txt` (from an older version), reconstruct one from `report.md`'s findings and coverage table first; if there is no `report.md`, write "No baseline for comparison". Fast reports are not compared against each other because each run overwrites the previous one.
- Use the full report template, omitting "Remediation Tasks" and capping "Suggested Rules" at 3 items; format front matter per the fast-mode example in the template.
- When there is no baseline, add a line in chat suggesting a normal checkup first.
