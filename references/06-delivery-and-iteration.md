# Dimension 6: Delivery & Iteration Governance

**Root cause**: Once a project runs, risk shifts to *how it changes* and *how it ships*. Release checklists that exist only in prose get skipped by AI; without tags and retained prior builds, you cannot roll back when something breaks; if a desktop app ships a crash-on-launch build, users have no idea they need to visit the website for a fix. Another hidden cost is **spinning in circles**: a bug AI has patched round after round without fixing, stacking workaround on workaround.

**Principle**: Enforce with code whatever can be enforced; keep an escape hatch on critical flows; cut losses early on stuck bugs.

**Items 6.3–6.6 are release checks**: run only for `pre-release` and `released`, and mark `N/A` for other stages. For `pre-release`, downgrade severities below by one level and note `upgrades to X after release` (see `agent-brief.md` Discipline #3); where an item explicitly defines a `pre-release` verdict, follow that item. Interpret by distribution method:
- **Installer / binary**: release = build, sign, upload; update = auto-update or in-app prompt; safety net = crash reporting + safe mode
- **Hosted service**: release = deploy; update = transparent to users; safety net = deployment rollback + feature flags
- **Run from source (`git clone`)**: release = git tag + CHANGELOG; update = whether dependencies, submodules, and build artifacts sync automatically after `git pull` (e.g., version/timestamp check at startup); safety net = whether the app boots with a clear warning when local data (config, memory, cache) is corrupted instead of crashing outright

---

### 6.1 ★ Git Fundamentals
- **Check**: scan §7: whether it is a git repo; commit granularity (share of oversized commits); vague commit messages; tracked build artifacts/logs/local databases; `.gitignore` coverage. Also check:
  - **Remote backup**: whether `git remote -v` is empty; if a remote exists, run `git status -sb` to check for large numbers of unpushed commits
  - **Uncommitted changes**: changes touching core flows, exceeding typical recent commit size, or sitting around for more than a day (check untracked file mtimes) all count as "long-standing uncommitted changes"
- **Verdict**: Core changes uncommitted with no remote backup → 🟠 (one misstep or dying drive loses everything). Only when scan §0/§7 says `not a git repository` does it count as not a repo → 🔴 (no history means no rollback if an agent breaks things). When it says `GIT ERROR` / `git failed`, git itself errored (e.g., permissions, `safe.directory`)—do not deduct points; escalate to the main agent. Large pileup of long-standing uncommitted changes → 🟠. Vague commits or oversized commits → 🟡 (cannot `git bisect` when regressions hit).

### 6.2 Branching & Parallel Development
- **Check**: Whether all features are developed straight on the main branch; whether branches or worktrees are used for parallel work; unpruned merged branches or stale worktrees (`git branch --merged`, `git worktree list`, checking last commit dates).
- **Verdict**: Developing multiple features in parallel directly on main → 🟡. Large pileup of stale branches/worktrees → ⚪/🟡.

### 6.3 Release Process Docs (Release Check)
- **Check**: Whether a documented release process exists: version bump, changelog, tests, build, signing/notarization, upload, website/store updates. **Single source of truth for version number**: verify version consistency across `package.json` / `Info.plist` / `build.gradle` / `pyproject.toml` / website or download page.
- **Verdict**: No release doc → 🟡; version maintained manually in multiple places and already out of sync → 🟠.

### 6.4 ★ Hard Gates (Release Check)
- **Check**: Which workflow steps are enforced programmatically: pre-commit / pre-push hooks, CI checks, release scripts (refusing to proceed if tests haven't run, version wasn't bumped, or changelog is missing). scan §0 lists detected CI and hooks; open them to see what they actually check.
- **Verdict**: Docs only with zero programmatic gates → 🟠 (AI will inevitably skip a step). Gates exist but are bypassed (`--no-verify` in scripts or rules) → 🟠.

### 6.5 ★ Rollback Capability (Release Check)
- **Check**: Whether every release is tagged; whether prior build artifacts are retained for redistribution; whether database migrations are reversible; whether remote config / feature flags can disable a feature without a new release; whether servers can one-click redeploy the previous version. **Local data formats** (config, saves, local DBs, caches): are they versioned? When a new version reads data written by an older version, does it migrate, read compatibly, error out, or silently reset?
- **Verdict**: Cannot revert to the previous version within 1 hour during an incident → 🔴 (paying users or a large user base) / 🟠. Upgrade makes old data unreadable or silently resets it → 🔴 (user data loss) / 🟠 (rebuildable cache).

### 6.6 ★ Crash Safety Net & Safe Mode (Release Check; Client Apps)
- **Check**:
  - Crash reporting in place
  - Startup crash-loop detection: after consecutive startup failures, does the app enter **safe mode**—disabling plugins / resetting suspect config, or at minimum showing a dialog telling the user how to update or recover?
  - Is safe mode minimal and decoupled from main-flow modules (so it cannot crash itself)?
  - Auto-update or in-app update reminder
  - Web apps: error boundaries, maintenance page, refresh prompt on frontend version mismatch
- **Verdict**: Client app with no user self-recovery path if a crash-on-launch build ships → 🔴. Safety net exists but safe mode shares heavy code with the main flow → 🟡.
- **Run from source** (no installer, crash reporting, or auto-update; per the distribution-method guide above, inspect local data only): corrupted local files (config, memory, saves, cache) cause a crash on launch requiring manual file repair → `released` 🟠, **`pre-release` 🟡 (upgrades to 🟠 after release)**; corrupted files silently overwritten causing data loss → same verdict, and also record under 2.5; quarantines the bad file and boots with defaults plus a warning → pass. Check every loader for bare `JSON.parse`—do not stop after checking just one (settings may be safe while memory or reminders are not).

### 6.7 Observability
- **Check**: Do logs carry enough context (request ID, version, key parameters)? Can issues be reproduced from user reports? Does error reporting cover both frontend and backend?
- **Verdict**: Released with zero error reporting → 🟠; otherwise 🟡.

### 6.8 ★ Bug-Churn Stop-Loss
- **Check**: scan §7 fix-churn hotspots (already restricted to code files with ≥2 fix commits). For the top 3–5 files, run `git log --oneline --follow -- <file> | head -30` to look for fix → fix → revert → fix loops. Inspect the code for signs of spinning in circles: layered workarounds, "temporary" comments, `setTimeout`/`sleep` timing hacks, stacked retries, multiple flags for the same bug. Distinguish **timing hacks** from **legitimate timers**: using a fixed delay to wait for something that has a real completion signal (event, Promise, callback, file lock) is a timing hack; UI animations, debounce, throttle, or polling with a comment explaining "no waitable signal exists" are legitimate timers. A single commented delay is not spinning.
- **Verdict**: Active churn loop → 🟠. The prescription is not "try fixing it again", but a **human decision item** in the report:
  1. Stop patching; have two strong models independently diagnose the root cause and state their confidence;
  2. Both ≥ ~90% confident and in agreement → fix the root cause per their plan;
  3. Both ≤ ~60% confident → the feature itself may be inherently intractable: cut it, or solve the underlying user need a different way. A bug AI struggles to diagnose will stay an ongoing maintenance burden after release.

### 6.9 Environment Isolation
- **Check**: Are dev/test/prod configs separated? Could tests hit production services or data? Do dev builds use separate data directories, bundle IDs, and ports so they do not pollute the daily-driver release build? Can desktop apps run in background/test mode? **When developing in parallel with multiple worktrees** (`git worktree list`), do app instances launched from different worktrees share the same user data directory, port, or single-instance lock—which causes them to overwrite each other's settings and prevents running concurrently?
- **Verdict**: Tests or dev builds could corrupt real data → 🟠/🔴; tangled configs → 🟡.

### 6.10 Fresh-Environment Runnability
- **Check**: Whether the next agent in a fresh worktree or on a fresh machine can get the project running by following the docs.
  - scan §0 "env vars read in code": env vars read by code that appear in neither env example files nor docs. Check each to see if it is required or has a default
  - Whether runtime versions are pinned (`.nvmrc` / `engines` / `.python-version` / `requires-python` / `rust-toolchain`)
  - Whether install and startup steps in README or rule files are complete (verify steps match files/scripts—do not execute)
- **Verdict**: Required env vars undocumented anywhere → 🟡; `pre-release` / `released` with `run from source` → 🟠 (users cannot run the project from README). No env example file when all variables have defaults → pass. Unpinned runtime version → ⚪.
