# Dimension 6: Delivery & Iteration Governance

**Principle**: Enforce with code what can be enforced; keep an escape hatch on critical flows; cut losses early on stuck bugs.

**Release checks (6.3–6.6)**: run only for `pre-release` and `released` (`N/A` otherwise). For `pre-release`, downgrade severity by one level vs. `released` and note `upgrades to X after release` (unless an item specifies its own `pre-release` verdict). Interpret by distribution method:
- **Installer / binary**: release = build, sign, upload; update = auto-update or in-app prompt; safety net = crash reporting + safe mode
- **Hosted service**: release = deploy; update = transparent; safety net = deployment rollback + feature flags
- **Run from source (`git clone`)**: release = git tag + CHANGELOG; update = auto-sync of deps/submodules/builds after `git pull`; safety net = boots with clear warning when local data (config, memory, cache) is corrupted

---

### 6.1 ★ Git Fundamentals
- **Check**:
  - Review scan §7 (git repo status, oversized commits, vague messages, bad tracked files, `.gitignore`).
  - **Remote backup**: check `git remote -v` and `git status -sb` for large unpushed commit backlogs.
  - **Long-standing uncommitted changes**: touching core flows, exceeding typical commit size, or >1 day old (check untracked file mtimes).
- **Verdict**:
  - 🔴: Only when scan §0/§7 reports `not a git repository`. (On `GIT ERROR` / `git failed`, do **not** deduct—escalate to main agent.)
  - 🟠: Uncommitted core changes with no remote backup; or large pileup of long-standing uncommitted changes.
  - 🟡: Vague or oversized commits.

### 6.2 Branching & Parallel Development
- **Check**: Parallel features developed directly on main; stale merged branches or worktrees (`git branch --merged`, `git worktree list`, last commit dates).
- **Verdict**:
  - 🟡: Multiple parallel features developed straight on main.
  - ⚪ / 🟡: Large pileup of stale branches/worktrees.

### 6.3 Release Process Docs (Release Check)
- **Check**: Documented release steps (version bump, changelog, tests, build, signing/notarization, upload, website/store updates) and **version SSOT** across `package.json` / `Info.plist` / `build.gradle` / `pyproject.toml` / website.
- **Verdict**:
  - 🟠: Version maintained manually in multiple places and already out of sync.
  - 🟡: No release doc.

### 6.4 ★ Hard Gates (Release Check)
- **Check**: Open CI and git hooks detected in scan §0 plus release scripts to verify what is enforced programmatically (tests, version bump, changelog).
- **Verdict**:
  - 🟠: Docs only with zero programmatic gates; or gates bypassed (`--no-verify` in scripts or rules).

### 6.5 ★ Rollback Capability (Release Check)
- **Check**: Release tags; retained prior build artifacts; reversible DB migrations; remote config / feature flags; one-click server redeploy; **versioned local data formats** (config, saves, local DBs, caches—migrate, read compatibly, error, or silently reset on upgrade?).
- **Verdict**:
  - 🔴: Cannot revert within 1 hour during an incident (paying or large user base); or upgrade makes old user data unreadable / silently resets it.
  - 🟠: Other rollback gaps; or silent reset of rebuildable cache.

### 6.6 ★ Crash Safety Net & Safe Mode (Release Check; Client Apps)
- **Check**:
  - Crash reporting; startup crash-loop detection entering minimal, decoupled **safe mode** (disable plugins / reset suspect config / show recovery dialog); auto-update or in-app update reminder.
  - Web apps: error boundaries, maintenance page, refresh prompt on frontend version mismatch.
- **Verdict (installer / hosted)**:
  - 🔴: Client app with no user self-recovery path if a crash-on-launch build ships.
  - 🟡: Safe mode shares heavy code with the main flow.
- **Run from source** (inspect local data loaders only—check **every** loader for bare `JSON.parse`, not just one):
  - Corrupted local files (config, memory, saves, cache) crash on launch → `released` 🟠; `pre-release` 🟡 (`upgrades to 🟠 after release`).
  - Corrupted files silently overwritten losing data → same verdict, plus record under 2.5.
  - Quarantines bad file and boots with defaults + warning → `pass`.

### 6.7 Observability
- **Check**: Log context (request ID, version, key params), reproducibility from user reports, error reporting coverage across frontend and backend.
- **Verdict**:
  - 🟠: `released` with zero error reporting.
  - 🟡: Otherwise.

### 6.8 ★ Bug-Churn Stop-Loss
- **Check**:
  - For the top 3–5 files in scan §7 fix-churn hotspots, run `git log --oneline --follow -- <file> | head -30` for fix → fix → revert → fix loops.
  - Inspect code for spinning signs: layered workarounds, `"temporary"` comments, `setTimeout`/`sleep` timing hacks, stacked retries, multiple flags for one bug.
  - **Distinguish timing hacks vs. legitimate timers**: fixed delay waiting for a real completion signal (event, Promise, callback, lock) = timing hack; UI animations, debounce, throttle, or polling commented `"no waitable signal exists"` = legitimate. A single commented delay is not spinning.
- **Verdict**:
  - 🟠: Active churn loop. Prescribe a **human decision item** (not "fix it again"):
    1. Stop patching; have two strong models independently diagnose root cause with confidence scores.
    2. Both ≥ ~90% confident and aligned → fix root cause per plan.
    3. Both ≤ ~60% confident → cut the feature or solve the underlying need differently.

### 6.9 Environment Isolation
- **Check**: Separated dev/test/prod configs; separate dev data dirs, bundle IDs, and ports; headless desktop test mode; **parallel worktrees** (`git worktree list`) sharing user data dir, port, or single-instance lock.
- **Verdict**:
  - 🔴 / 🟠: Tests or dev builds could corrupt real data.
  - 🟡: Tangled configs.

### 6.10 Fresh-Environment Runnability
- **Check**:
  - Scan §0 "env vars read in code" missing from env examples and docs (required vs. default).
  - Pinned runtime versions (`.nvmrc` / `engines` / `.python-version` / `requires-python` / `rust-toolchain`).
  - Complete install and startup steps in README/rules (verify against files/scripts without executing).
- **Verdict**:
  - 🟠: Required env vars undocumented on `pre-release` / `released` `run from source`.
  - 🟡: Required env vars undocumented otherwise.
  - ⚪: Unpinned runtime version.
  - `pass`: No env example file when all env vars have defaults.
