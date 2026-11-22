# Dimension 3: Docs & Rules

**Root cause**: AI loves writing proposals, and humans ask for them too. As features evolve, AI does not go back to update old docs, leaving the repo cluttered with expired proposals, plans, and notes. **Wrong docs are far worse than no docs**: with no docs, an agent reads the code; with wrong docs, an agent may skip verifying the code and build directly on stale facts, planting subtle bugs in downstream features.

Rule files (`AGENTS.md` / `CLAUDE.md`, etc.) are the flip side of the same coin: they sit in the agent's context on every turn, so one wrong rule causes repeated mistakes, and one missing rule causes repeated regressions.

---

### 3.1 ★ Doc Inventory & Classification
- **Check**: List all `.md`/`.mdx`/`.rst` docs and classify by purpose:
  - **Active specs** (README, architecture guides, design specs, API docs, agent rules): must match code
  - **Decision records** (why A was chosen over B): long-term value, should stay concise
  - **Proposals / plans** (feature implementation plans, TODOs, migration plans): should be archived or deleted once shipped
  - **Research notes & process logs**: generally should not remain on the main branch
  scan §5 lists plan-style docs, docs last modified >30 days before the latest code commit, and **git-ignored docs referenced by rule files** (local to the author's machine with no version history, making them the easiest to go stale). Classify every ignored doc too.
- **Verdict**: Completed-feature proposals still sitting in active directories and linked from rule files or README → 🟠; unlinked → 🟡. Prescription: distill still-valid decisions into active docs, then delete the rest or move them to `docs/archive/` (and state in rules that agents must not read `archive`).

### 3.2 ★ Doc–Code Consistency (Most Important Item in This Dimension)
- **Check**:
  1. Verify every item in scan §5 "docs citing code/doc paths that exist nowhere" (fenced code blocks, placeholders, and git-ignored build artifacts are already skipped, though some paths may still be runtime-generated outputs—distinguish them).
  2. For every **active spec** doc, sample 3–5 concrete verifiable claims (file locations, function/class names, commands, config keys, tech stack, data flow, directory conventions) and verify each against the code.
  3. Carefully verify commands in agent rule files and README against `package.json` scripts, `Makefile`, or actual files (check existence only—do not execute).
- **Verdict**:
  - 🔴: A doc that agents will read contains a statement contradicting code **that, if followed, will misdirect a core flow or architecture** (e.g., says data lives in A when it lives in B; says framework X is used after migrating to Y). If an always-loaded rule file (`AGENTS.md`, etc.) or the header comment of the modified file itself **explicitly states the correct rule** strongly enough to neutralize the wrong claim, downgrade to 🟠 and cite the exact neutralizing line in Evidence. **A generic "code takes precedence over docs" disclaimer alone is not enough** (it does not say which fact is right); only an affirmative statement about the specific fact neutralizes it. If only part of a wrong doc is neutralized, score based on the un-neutralized portion and note which parts are covered vs. not; if uncertain, mark `downgrade uncertain` and add it to "Decisions Needed".
  - 🟠: A doc that agents will read has multiple stale paths, commands, or names that waste time without breaking architecture.
  - 🟡: A single stale path, or staleness in a doc rarely read by agents.
  - Phrase every finding as "doc says X, code does Y".

### 3.3 ★ Agent Rule File Quality
- **Check**: `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` / `.cursorrules` / `.cursor/rules` / `copilot-instructions`, plus nested rule files in subdirectories (listed in scan §5).
  - **Duplicates**: Are multiple rule files or skill directories kept in sync via symlinks, includes, or a generator script, or maintained separately by hand? scan §4 "mirrored directory pairs" flags mirrored trees (e.g., `.claude/skills` ≡ `.agents/skills`). Hand-maintained copies inevitably drift.
  - **Length**: Beyond ~300 lines, attention gets diluted and adherence drops sharply in long sessions; check what should be pushed down into linked docs and whether the most critical rules sit at the top.
  - **Fluff**: Instructions models already follow by default ("write clean code", "pay attention to performance") do not change behavior—they only eat context.
  - **Essentials**: How to run **scoped** tests; paths to single sources of truth (tokens, shared components); directory conventions; known recurring pitfalls; doc maintenance rules (which doc to update when behavior changes); review focus areas.
- **Verdict**: Non-trivial project with no rule files at all → 🟠. Rules pointing to nonexistent targets or contradicting code → grade per 3.2. Hand-maintained copies that have already drifted → 🟠; still identical → 🟡. Missing essentials → 🟡/🟠. Heavy fluff → ⚪.

### 3.4 ★ Pitfalls vs. Rule Coverage (Within This Dimension)
- **Check**: Cross-check scan §7's fix-churn hotspot files and findings from this dimension against the rule files: is there a rule preventing each pitfall? Per-file churn misses pitfalls fixed across many files in a single commit, so also read the last 30 commit messages looking for sweep fixes ("fix review issues", "unify…", "all X should…") to identify what class of mistake was being cleaned up. Also check whether a review checklist exists (`review.md` or a review section in the rule file).
- **Verdict**: Recurring fix hotspots with no corresponding rule → 🟠. Draft one rule per gap for the main agent. (Cross-dimension recurring patterns are aggregated by the main agent in Step 3, not here.)

### 3.5 Doc Entry Points & Orphans
- **Check**: Whether README / rule files link to the docs agents need (architecture, design spec, release process). List docs referenced nowhere.
- **Verdict**: Key doc has no entry point → 🟡 (if an agent cannot find it, it might as well not exist). Orphan docs → delete or link, ⚪/🟡.

### 3.6 Doc Duplication & "Caching"
- **Check**: Same information written in multiple docs; docs restating facts easily queried from the environment (full `package.json` scripts lists, dependency versions, complete directory trees).
- **Verdict**: 🟡. Duplicated facts always drift. Prescription: keep one authoritative location and link from everywhere else; do not copy what can be read directly from the repo.

### 3.7 Proposal Quality (Inspect the Latest 1–3 Proposals)
- **Check**: Whether proposals are understandable and approvable by a project author who does not know the implementation language. Good proposals clearly cover:
  - How the UI will change (when UI exists)
  - Implementation approach and roughly what areas will be touched
  - Edge cases, special scenarios, and risks
  - Decisions requiring human input
  - Acceptance plan: what tests AI will run itself, and what flows the human should click through manually
  Two kinds of bad proposals: dense technical jargon the author cannot read; or merely rephrasing the requirement with no judgment, no risks, and no approach.
- **Verdict**: Recent proposals consistently lack decisions requiring human input or an acceptance plan → 🟡 (author cannot course-correct before coding or verify afterward). Projects with no proposal docs → N/A. Prescription: add a required-elements checklist for proposals to the rule file.
