# Fast Mode

Follows the five-step workflow in `SKILL.md`; only differences are listed below.

- **Scope**: check ★ items only; mark all others `not checked (fast mode)`.
- **Baseline**: latest normal checkup (`.vibe-checkup/report.md` + `scores.txt`). When valid, inspect only changes since baseline commit; otherwise inspect the whole project (still ★ items only).
- **Outputs**: write `.vibe-checkup/fast-report.md` and `fast-scores.txt`; never touch `report.md` or `scores.txt`.

## Step 1: Scope & Profile Card

After `baseline.py stamp`, determine incremental scope (if the baseline card lists excluded dirs, re-run with repeatable `--exclude <dir>`):

```bash
python <skill_dir>/scripts/baseline.py scope <project_root> [--exclude <dir>...]
```

Handle `verdict`:
- `empty`: no changes since baseline. Do not dispatch sub-agents; mark all items `carried from baseline` and note "No changes since baseline" in the report.
- `incremental`: scope = files under `changed:` (`A` added / `M` modified / `D` deleted / `?` untracked). Default threshold is 40% (override via `--threshold`). If baseline had `dirty: true`, uncommitted baseline files are re-included as changed.
- `full`: no usable baseline (`reason` states why: missing report / non-normal report / commit missing / >40% tracked files changed). Run full Step 1 profiling (★ items only), explain the reason in chat, and suggest running a normal checkup first.
- Exit code 2 or `git_error:`: stop and show raw error per `SKILL.md` Step 1.

**When a baseline exists**:
- Reuse the baseline profile card, updating only fields affected by changes, and save to `<temp_dir>/card.md`.
- Read only `scan.md` lines relevant to the change set, any README / rule files / manifests in the change set, and `git log --oneline <baseline_commit>..HEAD`.
- Carry stage from baseline; state `"Stage carried from baseline: X — let me know if this has changed"` in chat without waiting for confirmation.

## Step 2: Dispatch

- `≤ 10` changed files: run inline in main agent (still write findings to findings files).
- Otherwise (or when `full` with no baseline): use the 3-group split from `SKILL.md` Step 2 (A / B / C), regardless of project size.
- With baseline, pass `--since <baseline_commit>` to `scan.py`.
- Add to each sub-agent prompt: path to this file (instructing it to read "Incremental Scope Review Rules"), `"★ items only"`, change-set list (or `"no baseline"`), and relevant baseline findings.
- Extra verdicts: `not checked (fast mode)` and `carried from baseline`.
  - In `fast-scores.txt`, omit non-★ items and copy baseline verdicts for carried items (`5.4 🟡 carried from baseline` or `5.4 pass carried from baseline`).

## Incremental Scope Review Rules (Sub-Agents Read This)

- Run `scan.py --since <baseline_commit>` (§1–§3 filter to changed files, §2 pattern hits filter to changed lines, untracked files in full; §0 and §4–§8 stay whole-project). Grep callers repo-wide when a symbol is renamed or its signature changes.
- Inspect only changed files/lines. Reading outside scope for comparison (e.g., checking tokens or duplicate helpers) is allowed, but **do not report pre-existing issues in unchanged files**.
- **Baseline findings**:
  - No evidence file in change set → `carried from baseline` (do not re-check).
  - Any evidence file in change set → re-verify and note `still present` / `fixed` / `worsened`.
- Check items unrelated to changed files (e.g., manifests untouched → 5.4, 5.5) → `carried from baseline`.
- **Exception (3.2)**: if code behavior changed, reverse-check docs and rule files referencing those paths/behaviors even if those docs were not edited.
- **4.4**: run the "Name resolution" check (`references/04-tests.md` 4.4) on the incremental scope.

## Step 3: Verification

Run normal disproval verification on every 🔴/🟠 finding; skip second-model cross-verification.

## Step 4: Scoring, Comparison & Report

- Save ★-only score sheet to `.vibe-checkup/fast-scores.txt` and run `baseline.py score` (`carried from baseline` items score using their carried baseline verdicts).
- Compare against the same ★ item set in the baseline:
  ```bash
  python <skill_dir>/scripts/baseline.py score <project>/.vibe-checkup/scores.txt --items-from <project>/.vibe-checkup/fast-scores.txt
  ```
  - If baseline lacks `scores.txt` (older format), reconstruct it from `report.md`'s findings and coverage table first; if no `report.md`, write `"No baseline for comparison"`.
- Use `references/report-template.md` with fast-mode front matter, omitting "Remediation Tasks" and capping "Suggested Rules" at 3 items.
- If no baseline exists, suggest running a normal checkup first in chat.
