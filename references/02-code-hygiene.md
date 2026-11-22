# Dimension 2: Code Hygiene

**Root cause**: AI solves problems locally—hardcoding a value, copying a block of logic, keeping the old implementation as a fallback, propping up a screen with mock data, or writing a one-off probe script. Each shortcut saves effort in the moment, while piling up code that "looks like it works, but shouldn't exist". The next agent reads it, imitates it, and burns tokens on it.

`scan.py` already excludes vendored third-party directories (§0 "treated as vendored") and generated/minified files (§0 "generated/minified"). If it misclassified first-party project code as third-party, correct that first before proceeding.

---

### 2.1 ★ Hardcoded Values
- **Check**: scan §2's `hardcoded_color` / `hardcoded_size` / `hardcoded_endpoint` / `local_path`. Also check whether magic numbers (timeouts, retry counts, page sizes, thresholds, dimensions) and environment-dependent values (ports, domains, bucket names, model names, prices) are repeated across files:
  `git grep -nE "<suspicious_value>" -- <src_dir>`
- **Verdict**: Same value appears **≥3 times**, or varies by environment/machine yet is hardcoded → 🟠 (classic source of "updated one spot, missed the rest"). Appears 2 times → 🟡. Machine-specific absolute paths (`C:\…`, `D:\…`, `/Users/<name>/`) in runtime code → 🟠 (breaks on another machine); appearing only in hint copy, comments, or defaults with an env-var fallback → pass. Clear single-use local constant → pass. **Fixed protocol/format constants** (sample rates, magic file headers, spec constants other than standard ports, or app-defined default ports that can be overridden by config) repeated in multiple places cap at 🟡: they rarely change, though centralizing is still recommended. Hardcoded **non-configurable** ports or values that vary by environment/device still score 🟠 at ≥3 occurrences. For `hardcoded_endpoint` hits in files that look like provider or config tables (annotated by `scan.py`), verify whether the file itself is the single source of truth before flagging duplication.

### 2.2 ★ Duplicate Implementations
- **Check**: scan §4 "similar code blocks" catches literal duplication. Catch semantic duplication by reading: search by verb `git grep -nE "(function|def|func|fn) (format|parse|normalize|debounce|throttle|retry|fetch|load|save|validate|convert)\w*"` and compare same-named or near-synonymous helpers side by side. Check whether `utils/` or `helpers/` exists yet feature files still roll private copies.
- **Verdict**: Two implementations with **divergent behavior** (edge cases, units, timezones, rounding differ) → 🟠, a hidden bug factory. Identical behavior → 🟡. Specify which copy to keep.

### 2.3 ★ Stacked Fallbacks & Redundant Leftovers
- **Check**:
  - scan §2 `fallback_legacy` and `suspicious_filenames` (`old` / `backup` / `copy` / `v2` / `new` / `tmp`…)
  - Multiple code paths for the same feature: `try new path → catch → old path`, `if (useNewX)`, always-true/always-false feature flags
  - ≥5 consecutive lines of commented-out code
  - Unreferenced files and exports: **only when the tool is already installed**, run read-only—TS/JS `npx --no-install knip` or `npx --no-install ts-prune`, Python `vulture`, Go `deadcode`. If not installed, use standard grep: scan §2 `unreferenced_scripts` lists scripts whose names appear nowhere else; for suspicious exports, run `git grep -nw <export_name> -- . ':!<defining_file>'`—zero matches means a dead export. Do not run tools that require compiling the project (`cargo udeps`, `periphery`) during the checkup; suggest them in the prescription instead.
- **Verdict**: Calibrate by stage. Compatibility fallbacks for old data/APIs in an **unreleased** project → 🟠 (there are no legacy users—who is this protecting?). Fallbacks with a migration deadline in a released project → pass; without a deadline → 🟡. Dead files/exports → 🟡, or 🟠 in large volume.

### 2.4 ★ Placeholders & Mock Data
- **Check**: scan §2 `mock_data` and `todo_comment`; mock data in production paths, functions returning hardcoded success, `// TODO: hook up real API`, validation temporarily bypassed for debugging (`if (true)`, `skipAuth`, `return true // for now`), `sleep` waits standing in for real completion signals.
- **Verdict**: A feature users believe works that is actually fake → 🔴 (core flow) or 🟠. TODO comments on their own → ⚪, unless marking an unfinished core flow.

### 2.5 Error Handling (Check Both Extremes)
- **Check**:
  - Swallowed errors: scan §2 `swallowed_error`; critical paths (save, payment, export, sync) catching an error, logging, and continuing silently
  - Over-defensive code: repeated null checks on non-nullable values, wrapping every function in `try/catch`, validating the same input at every layer—a signature output of overly defensive models that buries real failures
  - User-visible error states: what does the user see on failure?
- **Verdict**: Silent failure on a critical path (potential data loss) → 🔴/🟠. Widespread over-defensive boilerplate → 🟡 (prescription: handle errors once at boundaries). Intentional ignores with an explanatory comment (e.g., optional asset load failure) → pass.

### 2.6 Type-Safety Escapes
- **Check**: scan §2 `type_escape_*` and `lint_disable_js`; whether `tsconfig` has `strict`; mypy/pyright config; Swift `!` force-unwraps and `try!`; whether lint rules have been disabled wholesale.
- **Verdict**: High density or concentrated in core modules → 🟡; type checking was once enabled and later turned off globally → 🟠 (deprives agents of their cheapest self-check). **Never enabled** (plain JS/Python with no `checkJs`, JSDoc types, or mypy) on a codebase over ~5,000 lines → 🟡, prescribing gradual adoption (e.g., `// @ts-check` at top of JS files); small projects → pass.

### 2.7 ★ God Files & Module Boundaries
- **Check**: scan §1. For files over ~800 lines (UI-related files: components, views, window scripts, regardless of language) or ~1,000 lines (other files), inspect whether they mix UI, state, IO, and business rules. List functions exceeding ~100 lines. In JS/TS, if `madge` is installed, run `npx --no-install madge --circular <entry>` to check circular dependencies.
- **Verdict**: Core functionality crammed into a single god file → 🟠: every agent edit must read the entire file, burning tokens and risking unintended edits to unrelated logic. Give concrete split boundaries in the prescription (by responsibility, not equal line counts). Oversized self-test/harness files → 🟡.

### 2.8 Debug Leftovers
- **Check**: scan §2 `debug_leftover` (already excludes CLI tools under `tools/`, `scripts/`, `cli/`). Left-on debug flags or test hooks shipped in production code.
- **Verdict**: Logs leaking sensitive data → 🟠; everything else → ⚪/🟡.

### 2.9 Over-Engineering
- **Check**: Abstract interfaces or factories with a single implementation, unused config options, plugin systems built "for the future", wrappers stacked around wrappers.
- **Verdict**: 🟡. Prescribe inlining and deletion. When an agent sees an abstraction, it assumes it is meant to be extended and piles on even more complexity.

### 2.10 One-Off Script Sprawl
- **Check**: scan §2 `one_off_scripts` (by filename) and `unreferenced_scripts` (filename mentioned nowhere else); clusters of undocumented scripts in the same directory also count. Inspect each: is it referenced by README, rule files, `package.json` scripts, or tests? Does the problem it investigated still exist?
- **Verdict**: Unreferenced probe scripts for already-solved issues → 🟡 (agents will treat them as active tools to read and maintain). Repeatedly used debug scripts → pass, though they should have entry-point documentation (cross-check 4.6).

### 2.11 Lying Comments & Edit Narration
- **Check**:
  - Edit narration: scan §2 `change_narration`—comments describing "what changed in this edit" (`// NEW:`, `// removed old logic`, `// changed as requested`, `// previously …`) rather than what the code does now. That belongs in commit messages.
  - Lying comments: sample 5 function headers, docstrings, or file-header comments from the 2–3 largest files in scan §1, and verify whether their stated parameters, return values, behavior, and call relationships match the code. Item 3.2 checks standalone docs; this item checks in-code comments—whatever file an agent edits, it reads the comments right there.
- **Verdict**: Comments in core modules contradicting the code → 🟠, written as "comment says X, code does Y"; isolated staleness → 🟡. Edit narration → ⚪, or 🟡 when pervasive (prescription: delete; history belongs in git).
