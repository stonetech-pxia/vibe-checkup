# Checkup Brief

Both the main agent and every sub-agent follow this document.

## Discipline

1. **Diagnose only—do not operate.**
   - Allowed directly: reading files; running this skill's `scan.py`; read-only git commands; static analysis tools **already installed locally** (for JS use `npx --no-install <tool>`; if not installed, skip and note `tool not installed` in the verdict).
   - Must ask the user first: running tests, launching the app, any command that downloads or installs over the network, and any tool that compiles the project (e.g., `cargo udeps`, `periphery scan`).
   - Only permitted write: `<project>/.vibe-checkup/`. Step 1's `baseline.py stamp` creates it with a single-line `*` `.gitignore` so the directory hides itself from git without touching the project's `.gitignore`; Step 4 writes the report and score sheet inside it (normal mode: `report.md`, `scores.txt`; fast mode: `fast-report.md`, `fast-scores.txt`). Scratch files (scan output, profile card, findings files) go in a temp directory, never inside the project. Do not modify code, delete files, or create files anywhere else.
   - **Sub-agents cannot ask the user**: skip anything that requires user permission, mark the verdict `needs approval, not run`, and provide a static assessment (potential side effects, estimated runtime, suggested command) so the main agent can roll it into "Decisions Needed" in the report.
2. **Leads ≠ Findings.** Output from `scan.py`, `grep`, or tools is only a lead. Open the file and confirm before calling anything a finding, and cite `path:line` evidence for every finding.
3. **Calibrate by stage.** Compatibility fallbacks in an unreleased prototype are pure waste; shipping without a rollback path to real users is critical. The same symptom carries different severity depending on stage. Choose one of four stages:
   - **`prototype`**: still validating the idea; no regular users
   - **`personal`**: used long-term by the author alone
   - **`pre-release`**: about to be handed to others for the first time (before open-sourcing, beta testing, or store submission). Run release-related checks as normal, downgrade severity by one level compared to `released`, and note `upgrades to X after release`
   - **`released`**: has users other than the author
   Also record the **distribution method**: `installer / binary`, `hosted service`, or `run from source (git clone)`. Interpret release checks in the reference docs according to the distribution method.
4. **Redact secrets everywhere.** Whenever citing a key, token, or password (in chat, sub-agent replies, or the report), show only the first 6 characters followed by `…`—never output the full value.

## Sub-Agent Assignment & Return Format

Read the profile card (path given in your prompt) and your assigned reference file(s), run the `scan.py` command from your prompt, and produce a verdict for **every check item** in the reference file. Each check item gets one verdict: `finding` / `pass` / `N/A (<one-line reason>)` / `needs approval, not run`. Missing even one item means the job is incomplete.

**Write findings to file—once.** Write full findings to the findings file specified in your prompt: start each dimension with `### Dimension N: Name`, use the "Finding Format" below, sort by severity, merge duplicates of the same kind, include at most 3 evidence locations plus total count, and keep code snippets to at most 5 lines. The report splices this file in directly, so it must stand on its own.

Everything you return stays in the main session's context for every remaining turn, so return only two things:

- ① A one-line summary per finding: `[🟠] 1.1 Title — path:line (N total)`. Do not repeat impact or prescription.
- ② A score sheet with one line per check item: `1.1 🟠` (highest severity finding for that item) / `1.2 pass` / `1.5 N/A (<one-line reason>)` / `5.4 needs approval, not run (static assessment and suggested command)`.
- Do not restate the task or narrate your process.
- Optionally add a short "Issues in Reference Docs" note at the end (items that were hard to execute, unclear thresholds, broken commands) to help improve this skill; omit if none.

## Finding Format

```
[🔴|🟠|🟡|⚪] <dimension.item> Title
- Evidence: path:line (list 1–3 more occurrences of the same kind, plus total count)
- Impact: how it misleads the next agent / harms users / slows iteration
- Prescription: concrete fix (where to edit, which single source of truth to converge on, what to delete)
- Effort: S (one agent, under an hour) / M (half a day) / L (needs splitting)
- Confidence: High / Medium / Low
```

The author of the finding fills in Confidence initially; the main agent re-checks it when verifying 🔴/🟠 findings.

## Severity Levels

- 🔴 **Critical**: risk of secret or user-data exposure; post-release crash with no user recovery path; a statement in docs or rules read by agents that contradicts code **and will misdirect a core flow or architecture** (a single stale path does not qualify); GPL/AGPL code in a closed-source commercial project; a core user flow that does not actually work.
- 🟠 **High**: structural problem that multiplies mess with every new feature—no single source of truth, multiple implementations of the same logic, stacked fallbacks, missing rules causing the same bug to recur.
- 🟡 **Medium**: localized mess that wastes tokens, slows iteration, or expands maintenance surface.
- ⚪ **Low**: hygiene and style issues.

Exact thresholds for each check item live in the dimension reference files and take precedence.
