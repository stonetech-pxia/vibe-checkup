# Vibe Checkup

An agent skill for running a health checkup on AI-iterated ("vibe-coded") projects.

Long-running AI-assisted projects rarely break all at once—they accumulate **sediment**: duplicate implementations, hardcoded values, stale design docs, missing agent rules, superficial tests, and unguarded releases. **Vibe Checkup** finds what will mislead the next agent or slow down maintenance, and outputs an evidence-backed report, ready-to-paste rules (`AGENTS.md` / `review.md`), and scoped remediation tasks.

**Diagnose only—never edits your code.** The only files written inside a scanned project live under `<project>/.vibe-checkup/` (which carries its own `*` `.gitignore` so it stays invisible to git).

## What It Checks

1. **Consistency & Single Source of Truth** — design tokens, shared components, interaction patterns, terminology, architecture
2. **Code Hygiene** — hardcoded values, duplicate logic, stacked fallbacks, mock/placeholder data, swallowed errors, god files, lying comments
3. **Docs & Rules** — doc rot, doc–code contradictions, `AGENTS.md`/`CLAUDE.md` quality, proposal quality
4. **Test Suite** — runnability, layering & scoped execution, superficial/brittle tests, critical-flow coverage, debug tooling
5. **Dependencies, Licenses & Security** — secrets, auth/authz, injection/misconfig, dependency health, license compliance
6. **Delivery & Iteration Governance** — git fundamentals, branching, release gates, rollback, crash safety net, bug-churn stop-loss, fresh-env setup

## Requirements

- **Python 3** (standard library only—no `pip install` needed)
- **Git** (optional, but recommended for history checks and fast incremental mode)

## Installation

### Claude Code

Install globally (available across all projects):

```bash
git clone https://github.com/stonetech-pxia/vibe-checkup.git ~/.claude/skills/vibe-checkup
```

On Windows (PowerShell):

```powershell
git clone https://github.com/stonetech-pxia/vibe-checkup.git "$HOME\.claude\skills\vibe-checkup"
```

Or install inside a single repository:

```bash
git clone https://github.com/stonetech-pxia/vibe-checkup.git .claude/skills/vibe-checkup
```

### Other Agent Skills Tools (Codex, Cursor, Antigravity, etc.)

Clone this repository into your tool's skills directory (for example `~/.agents/skills/vibe-checkup` or `<project>/.agents/skills/vibe-checkup`).

### Updating

```bash
git -C ~/.claude/skills/vibe-checkup pull
```

## Usage

Once installed, invoke the skill in your project session:

- **Full checkup (normal mode)** — creates/refreshes `.vibe-checkup/report.md` and `.vibe-checkup/scores.txt`:
  > "Run a vibe-checkup on this project."
  > "Do a health check before we start the next big feature."
- **Quick / incremental checkup (fast mode)** — checks ★ items only, scoped to changes since the last normal checkup, writing `.vibe-checkup/fast-report.md`:
  > "Run a quick vibe-checkup on recent changes."

### Standalone Mechanical Scan (Optional)

You can also run the read-only lead collector directly from the command line:

```bash
python scripts/scan.py /path/to/project
```

Use `--section 0,5,7` to print specific sections, or `--since <commit>` to scope sections §1–§3 to recent changes.

## Repository Structure

```text
vibe-checkup/
├── SKILL.md                 # Main five-step checkup workflow
├── references/
│   ├── agent-brief.md       # Shared discipline, finding format, and severity rules
│   ├── fast-mode.md         # Fast & incremental checkup rules
│   ├── report-template.md   # Output report template
│   └── 01–06-*.md           # Checklists for each of the six dimensions
└── scripts/
    ├── scan.py              # Read-only mechanical scanner (collects leads)
    └── baseline.py          # Baseline stamping, fast-mode scoping, scoring, and report assembly
```
