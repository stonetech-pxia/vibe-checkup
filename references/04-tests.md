# Dimension 4: Test Suite

**Root cause**: AI writes tests enthusiastically—especially unit tests—often producing piles of mechanical, superficial tests that assert constants, assert mocks were called, or assert "not null". They catch no real bugs yet break whenever implementation details shift, forcing agents to rewrite tests and waste tokens. On the other extreme, overly defensive models run the full suite after every one-line edit, burning 20 minutes of every hour waiting on tests.

Healthy state: **Layered tests, run only what you touched, save heavy suites for the end, true end-to-end verification for core user flows, and human sign-off for user experience.**

---

### 4.1 ★ Can the Tests Actually Run?
- **Check**: Find test commands (`package.json` scripts, `Makefile`, pytest config, Xcode schemes, CI config). Read test code and config to check whether running them hits real external services, writes to a real database, calls paid APIs, or writes snapshot files. **Ask the user before running tests**, specifying the exact command, estimated duration, and any files it may write (caches, snapshots). If approved, run only the fastest layer with snapshot-writing disabled (e.g., Jest `--ci`), in the background with a 5-minute timeout, and record pass count, failure count, and duration. If declined, do a static assessment only and note `not run` (or `needs approval, not run`) in the verdict.
- **Verdict**: Tests fail to run or have widespread unaddressed failures → 🟠 (green signal is broken; agents cannot self-verify). Unsafe side effects prevent running → 🟡 (missing environment isolation; see 6.9).

### 4.2 ★ Layering, Scoped Execution & Runtime
- **Check**: Are pure logic tests, UI tests, and E2E tests separated? Can you run tests for a single module (by path, tag, or target)? Do rule files specify "touch X → run only Y; run full suite after feature completion"? How long does the full suite take (from CI logs, 4.1 results, or estimated from test count)?
- **Verdict**: Full-suite-only execution → 🟡; slow full suite (>3 minutes) with no rule constraining run frequency → 🟠. Prescription: extract pure logic into standalone test modules, separate UI tests, and document scoped test commands in rule files.

### 4.3 ★ Superficial & Mechanical Tests
- **Check**: scan §6 weak-assertion counts. Also **sample 10 tests** across different modules, read them directly, and classify each:
  - Effective: verifies business rules, edge cases, or past regression bugs
  - Superficial: asserts constants/literals, `toBeDefined`/`toBeTruthy`/`NotNil`, or framework/language built-in behavior
  - Implementation mirror: copies implementation logic and compares against itself; mocks everything and asserts the mocks were called
  - Brittle: breaks when implementation details change even though user-visible behavior is unchanged
  When a test has multiple assertions, classify it by its **primary assertion** (what the test title promises to verify) and note issues with secondary assertions separately. Also note tests whose body never asserts what the title promises.
- **Verdict**: Superficial + mirror + brittle >40% of sample → 🟠; 20–40% → 🟡. Report the ratio and concrete examples; prescribe "draft a candidate deletion list for user approval before removing".

### 4.4 ★ Critical User Flow Coverage
- **Check**: Take each core user flow from the profile card and check whether an E2E/integration test or a repeatable script proves it works end-to-end (real clicks/calls, not stitched-together unit tests).
- **Verdict**: Core flows have zero end-to-end verification → 🟠. Evidence that a core flow is currently broken → 🔴. Item 4.4 is not a release check and is **never downgraded for stage**: lacking end-to-end verification blinds agents from self-checking regardless of whether external users exist. If git history shows fixes like "unit tests all green, crashed on launch", cite them as evidence.
- **Name resolution** (check only on modified files: fast-mode incremental scope and after Step 5 execution in `SKILL.md`; dynamic languages only—JS, Python, Lua, Ruby, PHP, etc.; skip compiled languages like Swift, Kotlin, Rust, Go where the compiler guarantees this): verify that every function, variable, class, or module name newly referenced in changed lines is defined or imported/required in that file. If a linter is installed locally, run it only on the modified files (more accurate than eyeballing diffs): for JS with an existing eslint config run `npx --no-install eslint <changed_files>` and check `no-undef`-like errors; for Python run `ruff check --select F821 <changed_files>` or `python -m pyflakes <changed_files>`. Never pass `--fix`. If no linter is installed, inspect the diff statically. Report missing symbols under 4.4, noting "only surfaces at startup or runtime": 🔴 if on a startup path or core flow (core flow actually broken), otherwise 🟠. This is the cheapest line of defense for startup paths untouched by `npm test`.

### 4.5 Skipped, Disabled & Always-Green Tests
- **Check**: scan §6 `skipped/only` count; commented-out assertions; `|| true` in test scripts; `continue-on-error` in CI; tests that catch exceptions and pass anyway.
- **Verdict**: 🟡; masking known failures → 🟠.

### 4.6 ★ Programmatic Debug Tools
- **Check**: Are frequently debugged flows (file uploads, login, complex action sequences) wrapped in CLIs, scripts, or test helpers so an agent can reproduce them with a few arguments instead of clicking through via browser-use / computer-use every time? Are there test data seeds/fixtures? Can desktop apps run tests headless / in the background without stealing focus from the user's screen?
- **Verdict**: Repeatedly walking the same flow manually with no tooling → 🟡 (name the flows worth wrapping in the report).

### 4.7 Manual UX Acceptance
- **Check**: AI-driven E2E tests only prove a flow executes; only a human can judge whether the interaction feels smooth and the design looks right. Does the project have a pre-release human walkthrough checklist (core flows, new features, regression-prone interactions)? Do proposals or PRs include manual acceptance steps?
- **Verdict**: Released project with UI and no manual acceptance checklist → 🟡; `pre-release` → ⚪, noting "add before first release". Prescription: derive a 5–10 item checklist from the core user flows and place it in the release process doc.

### 4.8 Performance Baselines (Performance-Sensitive Projects Only)
Performance-sensitive means projects where users directly feel latency or smoothness: real-time audio/video, games and animations, large lists or large file processing, frequently launched desktop tools, or services with SLAs. Example metrics: time to first token/speech, frame rate, startup time, P95 latency.
- **Check**: Is there a repeatable benchmark script and recorded baseline numbers? Are performance targets realistic? Are there signs of repeatedly chasing an impossible target and making code messier (multiple rounds of "optimize" commits on the same file)?
- **Verdict**: Performance-sensitive with no baseline → 🟡; chasing unrealistic targets and adding complexity → 🟠.
