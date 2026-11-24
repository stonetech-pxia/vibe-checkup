# Dimension 2: Code Hygiene

Verify scan §0's `treated as vendored` and `generated/minified` lists first—if first-party code was misclassified, include it in your review.

---

### 2.1 ★ Hardcoded Values
- **Check**:
  - Review scan §2 `hardcoded_color` / `hardcoded_size` / `hardcoded_endpoint` / `local_path`.
  - Check repeated magic numbers (timeouts, retries, page sizes, thresholds, dimensions) and environment-dependent values (ports, domains, bucket names, model names, prices):
    ```bash
    git grep -nE "<suspicious_value>" -- <src_dir>
    ```
- **Verdict**:
  - 🟠: Same value repeated ≥3 times; any environment/machine-dependent value (including non-configurable ports) hardcoded in runtime code; machine-specific absolute paths (`C:\…`, `D:\…`, `/Users/<name>/`) in runtime code.
  - 🟡: Repeated 2 times; or repeated fixed protocol/format constants (sample rates, magic file headers, non-standard spec constants, overridable app default ports—cap at 🟡).
  - `pass`: Single-use local constant; paths only in hint copy, comments, or env-var fallbacks; provider/config tables (annotated by `scan.py`) that *are* the SSOT.

### 2.2 ★ Duplicate Implementations
- **Check**:
  - Review scan §4 "similar code blocks" for literal duplication.
  - Check semantic duplication by verb and compare against `utils/` / `helpers/`:
    ```bash
    git grep -nE "(function|def|func|fn) (format|parse|normalize|debounce|throttle|retry|fetch|load|save|validate|convert)\w*"
    ```
- **Verdict**:
  - 🟠: ≥2 implementations with **divergent behavior** (edge cases, units, timezones, rounding).
  - 🟡: Identical behavior. Always specify which copy to keep.

### 2.3 ★ Stacked Fallbacks & Redundant Leftovers
- **Check**:
  - Scan §2 `fallback_legacy` and `suspicious_filenames` (`old` / `backup` / `copy` / `v2` / `new` / `tmp`…).
  - Multiple paths for the same feature (`try new → catch → old`, `if (useNewX)`, always-true/false feature flags).
  - ≥5 consecutive lines of commented-out code.
  - Unreferenced files/exports: run read-only **only if already installed** (`npx --no-install knip`, `npx --no-install ts-prune`, `vulture`, `deadcode`); otherwise inspect scan §2 `unreferenced_scripts` and grep suspicious exports:
    ```bash
    git grep -nw <export_name> -- . ':!<defining_file>'
    ```
    Do not run compile-requiring tools (`cargo udeps`, `periphery`)—suggest them in prescription instead.
- **Verdict**:
  - 🟠: Compatibility fallbacks for old data/APIs in an **unreleased** project; dead files/exports in large volume.
  - 🟡: Fallbacks in a `released` project without a migration deadline; isolated dead files/exports.
  - `pass`: Fallbacks in a `released` project with an explicit migration deadline.

### 2.4 ★ Placeholders & Mock Data
- **Check**: Scan §2 `mock_data` and `todo_comment`; mock data on production paths; hardcoded success returns; `// TODO: hook up real API`; debug auth/validation bypasses (`if (true)`, `skipAuth`, `return true // for now`); `sleep` standing in for real completion signals.
- **Verdict**:
  - 🔴: Fake/stubbed implementation on a core user flow.
  - 🟠: Fake/stubbed non-core feature.
  - ⚪: Standalone TODO comments (unless marking an unfinished core flow).

### 2.5 Error Handling (Check Both Extremes)
- **Check**:
  - Swallowed errors: scan §2 `swallowed_error`; critical paths (save, payment, export, sync) catching, logging, and continuing silently.
  - Over-defensive boilerplate: repeated null checks on non-nullable values, `try/catch` around every function, re-validating the same input at every layer.
  - User-visible error states on failure.
- **Verdict**:
  - 🔴 / 🟠: Silent failure on a critical path (potential data loss).
  - 🟡: Widespread over-defensive boilerplate (prescription: handle errors once at boundaries).
  - `pass`: Intentional ignore with an explanatory comment (e.g., optional asset load).

### 2.6 Type-Safety Escapes
- **Check**: Scan §2 `type_escape_*` and `lint_disable_js`; `tsconfig` `strict`; mypy/pyright config; Swift `!` / `try!`; wholesale lint disables.
- **Verdict**:
  - 🟠: Type checking was previously enabled and later disabled globally.
  - 🟡: High density of escapes or concentrated in core modules; or type checking **never enabled** (no `checkJs`/JSDoc/mypy) on a codebase >~5,000 lines (prescribe gradual adoption, e.g., `// @ts-check`).
  - `pass`: Untyped small project (≤~5,000 lines).

### 2.7 ★ God Files & Module Boundaries
- **Check**:
  - Review scan §1: inspect files >~800 lines (UI-related files regardless of language) or >~1,000 lines (other files) for mixed UI, state, IO, and business rules.
  - List functions >~100 lines.
  - JS/TS: if `madge` is installed, run `npx --no-install madge --circular <entry>`.
- **Verdict**:
  - 🟠: Core functionality crammed into a god file (prescribe concrete split boundaries by responsibility, not equal line counts).
  - 🟡: Oversized self-test/harness files.

### 2.8 Debug Leftovers
- **Check**: Scan §2 `debug_leftover`; active debug flags or test hooks shipped in production code.
- **Verdict**:
  - 🟠: Logs leaking sensitive data.
  - ⚪ / 🟡: Other debug leftovers.

### 2.9 Over-Engineering
- **Check**: Single-implementation interfaces/factories, unused config options, speculative plugin systems, wrappers around wrappers.
- **Verdict**:
  - 🟡: Prescribe inlining and deletion.

### 2.10 One-Off Script Sprawl
- **Check**: Scan §2 `one_off_scripts` and `unreferenced_scripts`, plus clusters of undocumented scripts. Check whether each is referenced by README, rule files, `package.json` scripts, or tests, and whether its target issue still exists.
- **Verdict**:
  - 🟡: Unreferenced probe scripts for already-solved issues.
  - `pass`: Repeatedly used debug scripts (should still have entry-point docs; cross-check 4.6).

### 2.11 Lying Comments & Edit Narration
- **Check**:
  - Edit narration: scan §2 `change_narration` (`// NEW:`, `// removed old logic`, `// changed as requested`, `// previously …`).
  - Lying comments: sample 5 function headers, docstrings, or file-header comments from the 2–3 largest files in scan §1 and verify parameters, returns, behavior, and call relationships against code.
- **Verdict**:
  - 🟠: Comments in core modules contradicting code (phrase as `"comment says X, code does Y"`).
  - 🟡: Isolated stale comments; pervasive edit narration (prescribe deletion).
  - ⚪: Isolated edit narration.
