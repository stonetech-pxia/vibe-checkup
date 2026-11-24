# Dimension 4: Test Suite

**Target state**: Layered tests, scoped execution per module, full suite at feature end, real end-to-end verification for core flows, and manual UX sign-off.

---

### 4.1 ★ Can the Tests Actually Run?
- **Check**:
  - Locate test commands (`package.json`, `Makefile`, pytest, Xcode schemes, CI).
  - Statically check whether running tests hits external services, writes to a real DB, calls paid APIs, or writes snapshots.
  - **Ask user before running** (state exact command, estimated duration, and writable files).
  - If approved: run only the fastest layer with snapshot-writing disabled (e.g., Jest `--ci`), in background, 5-minute timeout; record pass/fail counts and duration.
  - If declined: static assessment only, mark `not run`.
- **Verdict**:
  - 🟠: Tests fail to run or have widespread unaddressed failures.
  - 🟡: Unsafe side effects block running (missing isolation; see 6.9).

### 4.2 ★ Layering, Scoped Execution & Runtime
- **Check**: Are pure logic, UI, and E2E tests separated? Can a single module be run (by path, tag, or target)? Do rule files define scoped vs. full-suite run policy? Estimate full-suite runtime (CI logs, 4.1 run, or test count).
- **Verdict**:
  - 🟠: Slow full suite (>3 min) with no rule constraining run frequency.
  - 🟡: Full-suite-only execution (prescribe separating pure logic/UI tests and documenting scoped commands in rule files).

### 4.3 ★ Superficial & Mechanical Tests
- **Check**: Review scan §6 weak-assertion counts, and **sample 10 tests** across modules. Classify each by its **primary assertion** (what the title promises; note secondary assertion issues and title–body mismatches separately):
  - **Effective**: verifies business rules, edge cases, or past regressions
  - **Superficial**: asserts constants/literals, `toBeDefined`/`toBeTruthy`/`NotNil`, or built-in behavior
  - **Implementation mirror**: duplicates implementation logic or mocks everything to assert mock calls
  - **Brittle**: breaks on internal refactors despite unchanged user-visible behavior
- **Verdict**:
  - 🟠: Superficial + mirror + brittle >40% of sample.
  - 🟡: 20–40%.
  - Report ratio + examples; prescribe drafting a candidate deletion list for user approval.

### 4.4 ★ Critical User Flow Coverage
- **Check**: For each core user flow on the profile card, verify whether an E2E/integration test or repeatable script exercises it end-to-end (real clicks/calls, not unit tests). Cite git history like `"unit tests all green, crashed on launch"` if present.
- **Verdict** (**never downgraded for stage**):
  - 🔴: Evidence a core flow is currently broken.
  - 🟠: Zero end-to-end verification for core flows.
- **Name resolution** (modified files only—fast-mode incremental scope and after Step 5 execution; **dynamic languages only** such as JS, Python, Lua, Ruby, PHP; skip compiled languages like Swift, Kotlin, Rust, Go):
  - Verify every symbol/module newly referenced in changed lines is defined or imported in that file.
  - Run a locally installed linter on modified files only (never pass `--fix`):
    - JS (with existing eslint config): `npx --no-install eslint <changed_files>` (check `no-undef`-like errors)
    - Python: `ruff check --select F821 <changed_files>` or `python -m pyflakes <changed_files>`
    - Otherwise inspect the diff statically.
  - Report missing symbols under 4.4 noting `"only surfaces at startup or runtime"`: 🔴 on a startup path or core flow, else 🟠.

### 4.5 Skipped, Disabled & Always-Green Tests
- **Check**: Scan §6 `skipped/only` counts; commented-out assertions; `|| true` in test scripts; `continue-on-error` in CI; tests catching exceptions and passing anyway.
- **Verdict**:
  - 🟠: Masking known failures.
  - 🟡: Other skipped/disabled test buildup.

### 4.6 ★ Programmatic Debug Tools
- **Check**: Are frequently debugged flows (uploads, login, complex sequences) wrapped in CLIs, scripts, or helpers? Are test seeds/fixtures present? Can desktop apps run headless/background without stealing focus?
- **Verdict**:
  - 🟡: Repeated manual walkthroughs with no tooling (name flows worth wrapping).

### 4.7 Manual UX Acceptance
- **Check**: Does a pre-release human walkthrough checklist exist (core flows, new features, regression-prone interactions)? Do proposals/PRs include manual acceptance steps?
- **Verdict**:
  - 🟡: `released` UI project with no manual acceptance checklist (prescribe a 5–10 item checklist in the release doc).
  - ⚪: `pre-release` (note `"add before first release"`).

### 4.8 Performance Baselines (Performance-Sensitive Projects Only)
Applies where users directly feel latency/smoothness (real-time audio/video, games/animations, large lists/files, frequent desktop tools, SLA services; e.g., TTFT/speech, FPS, startup time, P95).
- **Check**: Repeatable benchmark script + recorded baseline? Realistic targets? Multi-round `"optimize"` commit churn on the same file?
- **Verdict**:
  - 🟠: Chasing unrealistic targets and adding complexity.
  - 🟡: Performance-sensitive with no baseline.
