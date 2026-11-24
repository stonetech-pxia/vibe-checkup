# Checkup Brief

Applies to both the main agent and every sub-agent.

## Discipline

1. **Diagnose only—do not operate.**
   - **Allowed directly**: reading files; running `scan.py` as a black box (do not read script source); read-only git commands; static analysis tools **already installed locally** (JS: `npx --no-install <tool>`; if missing, skip and note `tool not installed`).
   - **Must ask user first**: running tests, launching the app, network downloads/installs, and tools that compile the project (e.g., `cargo udeps`, `periphery scan`).
   - **Only permitted write**: `<project>/.vibe-checkup/` (created with a `*` `.gitignore` by `baseline.py stamp`; Step 4 writes `report.md`/`scores.txt` or `fast-report.md`/`fast-scores.txt`). Put scratch files (scan output, profile card, findings files) in a temp directory, never inside the project. Do not modify, create, or delete anything else.
   - **Sub-agents cannot ask the user**: skip approval-gated checks, mark `needs approval, not run`, and attach a static assessment (side effects, estimated runtime, suggested command) for "Decisions Needed".
2. **Leads ≠ Findings.** `scan.py`, `grep`, and tool hits are leads only—open the file to confirm and cite `path:line` evidence for every finding.
3. **Calibrate by stage** (and record **distribution method**: `installer / binary`, `hosted service`, or `run from source (git clone)`):
   - **`prototype`**: validating idea; no regular users
   - **`personal`**: long-term solo use by author
   - **`pre-release`**: about to ship externally (open-source, beta, store); run release checks normally, downgrade severity by one level vs. `released`, and note `upgrades to X after release`
   - **`released`**: has users other than the author
4. **Redact secrets everywhere** (chat, sub-agent replies, report): show only the first 6 characters followed by `…`.

## Sub-Agent Assignment & Return Format

Read `<temp_dir>/card.md` and your assigned reference file(s), run the `scan.py` command in your prompt, and produce a verdict for **every check item**: `finding` / `pass` / `N/A (<one-line reason>)` / `needs approval, not run`.

**Findings file** (spliced directly into the report):
- Start each dimension with `### Dimension N: Name`.
- Use the Finding Format below, sorted by severity.
- Merge duplicates of the same kind; cite ≤3 evidence locations + total count; keep code snippets ≤5 lines.

**Chat return** (stays in main-session context—keep minimal):
1. One-line summary per finding: `[🟠] 1.1 Title — path:line (N total)` (no impact or prescription).
2. Score sheet, one line per check item: `1.1 🟠` (highest severity) / `1.2 pass` / `1.5 N/A (<reason>)` / `5.4 needs approval, not run (<static assessment & command>)`.
3. Do not restate the task or narrate your process.
4. Optional short "Issues in Reference Docs" note (unclear thresholds, broken commands); omit if none.

## Finding Format

```
[🔴|🟠|🟡|⚪] <dimension.item> Title
- Evidence: path:line (1–3 more occurrences of the same kind, plus total count)
- Impact: how it misleads the next agent / harms users / slows iteration
- Prescription: concrete fix (where to edit, SSOT to converge on, what to delete)
- Effort: S (<1 hr, one agent) / M (half day) / L (needs splitting)
- Confidence: High / Medium / Low
```

Initial `Confidence` is set by the author and re-checked by the main agent for 🔴/🟠 findings.

## Severity Levels

- 🔴 **Critical**: secret/user-data exposure risk; post-release crash with no user recovery path; agent-read doc/rule contradicting code **in a way that misdirects a core flow or architecture** (a single stale path does not qualify); GPL/AGPL in a closed-source commercial project; broken core user flow.
- 🟠 **High**: structural issue that multiplies mess per feature—missing SSOT, duplicate implementations, stacked fallbacks, missing rules causing recurring bugs.
- 🟡 **Medium**: localized mess that wastes tokens, slows iteration, or expands maintenance surface.
- ⚪ **Low**: hygiene and style issues.

Item-level thresholds in `references/01–06-*.md` take precedence.
