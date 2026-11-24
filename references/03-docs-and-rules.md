# Dimension 3: Docs & Rules

---

### 3.1 ★ Doc Inventory & Classification
- **Check**: List all `.md`/`.mdx`/`.rst` docs—plus every **git-ignored doc referenced by rule files** (scan §5)—and classify:
  - **Active specs** (README, architecture, design specs, API docs, agent rules): must match code
  - **Decision records** (why A over B): concise, long-term value
  - **Proposals / plans** (feature plans, TODOs, migration plans): archive or delete once shipped
  - **Research notes & process logs**: should not remain on main branch
  - Review scan §5 plan-style docs and docs last modified >30 days before the latest code commit.
- **Verdict**:
  - 🟠: Completed-feature proposals still in active directories and linked from rule files or README.
  - 🟡: Unlinked completed proposals.
  - Prescription: distill still-valid decisions into active docs; delete the rest or move to `docs/archive/` (and add a rule telling agents not to read `archive`).

### 3.2 ★ Doc–Code Consistency (Highest-Impact Item)
- **Check**:
  1. Verify every item in scan §5 "docs citing code/doc paths that exist nowhere" (distinguish runtime-generated outputs from genuinely stale paths).
  2. For every **active spec**, sample 3–5 concrete verifiable claims (file locations, symbol names, commands, config keys, tech stack, data flow, directory conventions) and verify against code.
  3. Verify commands in rule files and README against `package.json` scripts, `Makefile`, or actual files (check existence only—do not execute).
- **Verdict** (phrase every finding as `"doc says X, code does Y"`):
  - 🔴: An agent-read doc contradicts code **in a way that misdirects a core flow or architecture** (e.g., wrong data location, pre-migration framework).
    - **Downgrade (`🔴 → 🟠`)**: Only if an always-loaded rule file (`AGENTS.md`, etc.) or the edited file's header comment **explicitly states the specific correct rule** strongly enough to neutralize the wrong claim (cite the exact line in Evidence). A generic `"code takes precedence over docs"` disclaimer does **not** neutralize it.
    - For partially neutralized claims, grade on the un-neutralized ones and note coverage; if uncertain, mark `downgrade uncertain` and add to "Decisions Needed".
  - 🟠: Agent-read doc has multiple stale paths, commands, or names that waste time without breaking architecture.
  - 🟡: Single stale path, or staleness in a doc rarely read by agents.

### 3.3 ★ Agent Rule File Quality
- **Check**: Inspect `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` / `.cursorrules` / `.cursor/rules` / `copilot-instructions` and nested subdirectory rule files (scan §5):
  - **Duplicates**: Check scan §4 "mirrored directory pairs" (e.g., `.claude/skills` ≡ `.agents/skills`) and multiple rule files—synced via symlinks/includes/generator, or hand-maintained?
  - **Length**: >~300 lines dilutes attention—check what can move to linked docs and whether critical rules sit at the top.
  - **Fluff**: Generic advice models already follow (`"write clean code"`, `"pay attention to performance"`).
  - **Essentials**: Scoped test commands; SSOT paths (tokens, shared components); directory conventions; recurring pitfalls; doc update rules; review focus areas.
- **Verdict**:
  - 🟠: Non-trivial project with no rule files; hand-maintained copies that have already drifted; missing critical essentials.
  - Rules citing nonexistent targets or contradicting code → grade per 3.2.
  - 🟡: Hand-maintained copies still identical; minor missing essentials.
  - ⚪: Heavy fluff.

### 3.4 ★ Pitfalls vs. Rule Coverage (Within This Dimension)
- **Check**:
  - Cross-check scan §7 fix-churn hotspots and this dimension's findings against rule files.
  - Read the last 30 commit messages for sweep fixes (`"fix review issues"`, `"unify…"`, `"all X should…"`) that per-file churn misses.
  - Check whether a review checklist exists (`review.md` or a review section in the rule file).
- **Verdict**:
  - 🟠: Recurring fix hotspots with no corresponding rule (draft one rule per gap; cross-dimension patterns are aggregated by the main agent in Step 3).

### 3.5 Doc Entry Points & Orphans
- **Check**: Verify README / rule files link to needed docs (architecture, design spec, release process); list unreferenced orphan docs.
- **Verdict**:
  - 🟡: Key doc has no entry point.
  - ⚪ / 🟡: Orphan docs (link or delete).

### 3.6 Doc Duplication & "Caching"
- **Check**: Same information repeated across docs; docs copying facts queryable from the repo (full `package.json` scripts, dependency versions, full directory trees).
- **Verdict**:
  - 🟡: Keep one authoritative location and link from elsewhere; delete copied repo facts.

### 3.7 Proposal Quality (Latest 1–3 Proposals)
- **Check**: Verify proposals are understandable and approvable by a project author who may not know the implementation language. Required elements:
  - UI changes (when UI exists)
  - Implementation approach and touched areas
  - Edge cases, special scenarios, and risks
  - Decisions requiring human input
  - Acceptance plan (automated tests vs. manual human walkthroughs)
  - Flag dense jargon or mere requirement restatement with no approach/risks.
- **Verdict**:
  - 🟡: Recent proposals consistently lack human decisions or an acceptance plan (prescribe adding a required-elements checklist to the rule file).
  - `N/A`: No proposal docs.
