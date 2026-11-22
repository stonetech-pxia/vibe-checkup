# Dimension 5: Dependencies, Licenses & Security

**Root cause**: AI optimizes for "make it run": dropping secrets straight into code, checking auth only on the frontend, leaving database rules wide open, pulling in unfamiliar packages on a whim, and pasting open-source code without checking its license. Not a big deal in the prototype stage, but once real users or commercial use arrive, any one of these can become an incident.

(See `agent-brief.md` Discipline #4 for secret redaction rules.)

---

### 5.1 ★ Secrets & Credentials
- **Check**:
  - scan §3 (scans git-tracked and non-ignored files; values are already redacted)
  - Whether `.env` is ignored: `git check-ignore -v .env`
  - Secrets in git history: `git log --all -S "<suspicious_prefix>" --format="%h %ad %s"` (list commits only—do not print contents). This also matches provider-prefix detection code and dummy test values, so open matching commits to check whether the matched string has real-key length or is a placeholder like `test`/`fake`/`xxx`
  - Server-side secrets leaked to clients: `NEXT_PUBLIC_*` / `VITE_*` / `EXPO_PUBLIC_*` variables containing `SECRET`/`KEY`/`TOKEN`; API keys bundled into Electron renderers, iOS/Android builds, or browser extensions
- **Verdict**: Real secret in code or git history → 🔴 (prescription: revoke and rotate first, then scrub; merely deleting from code is insufficient). Server-side secret exposed to client → 🔴.

### 5.2 ★ Authentication & Authorization
- **Check**: Whether every backend route / cloud function enforces auth; whether authorization is checked only on the frontend; whether resource lookups by ID verify ownership (IDOR); whether Supabase RLS is enabled or Firebase rules are left as `if true`; whether admin or debug endpoints are exposed.
- **Verdict**: Any gap involving real user data → 🔴; in `prototype` stage → 🟠 with note `must fix before launch`.
- **Desktop app local endpoints** (local WebSocket/HTTP, IPC) are judged separately as follows: binding strictly to `127.0.0.1` and rejecting requests with an `Origin` header is the baseline—missing either → 🟠 (any web page can invoke it); baseline present but no auth token, allowing other local processes to connect and read sensitive data like screenshots, transcripts, or files → 🟡; binding to `0.0.0.0` → 🔴.
- **Metered / paid endpoints**: Does the backend proxy LLMs, SMS, email, or other pay-per-use third-party APIs? Does it enforce auth and rate limiting (per user or IP)? Do retries, polling loops, and agent loops have upper bounds? Unauthenticated paid endpoint callable by anyone → 🔴 if external users exist, otherwise 🟠 with note `must fix before launch`; authenticated but no rate limit, or unbounded loops → 🟡.

### 5.3 Injection, Dangerous APIs, Misconfiguration & Privacy
- **Check**:
  - Injection: SQL string concatenation; `eval` / `exec` / `new Function`; `dangerouslySetInnerHTML` / `v-html` / `innerHTML` with user input; interpolating user input into shell commands; unnormalized file paths; server-side requests to user-supplied URLs (SSRF)
  - Electron: `nodeIntegration: true`, `contextIsolation: false`, `webSecurity: false`
  - **Desktop shell projects only** (has `BrowserWindow` / `preload` / `ipcMain`, or `tauri.conf`; skip this sub-check otherwise and still check the rest of 5.3): does `preload` expose unrestricted `send`/`on` to the renderer (should allowlist channel names)? Are navigation guards like `setWindowOpenHandler` and `will-navigate` in place? Do windows load only local content? Generic IPC bridge loading only local content → ⚪; loading external pages or user content without guards → 🟠.
  - Configuration: `*` CORS with credentials; debug mode on in production; raw stack traces returned to clients; default passwords; publicly writable storage buckets
  - Privacy: PII, tokens, or full request bodies in logs; unconsented telemetry; sensitive data stored locally in plaintext
- **Verdict**: Reachable by user input or involving real user data → 🔴/🟠; trusted internal input only or `prototype` stage → 🟡.

### 5.4 ★ Dependency Health
- **Check**:
  - Dependency count (scan §0 lists every `package.json`); multiple libraries serving the same role (`axios` + `ky` + custom `fetch` wrapper; `moment` + `dayjs`; two UI libraries) → if the same root cause as 1.7, score in one place only
  - Unused dependencies: **when already installed**, run `npx --no-install depcheck` or `npx --no-install knip`
  - **Hallucinated / typosquatted packages**: verify unfamiliar package names exist and have normal download volume (`npm view <pkg> name version`, `pip index versions <pkg>`—read-only lookups), paying extra attention to names 1–2 characters off from popular packages
  - Known vulnerabilities: `npm audit --omit=dev` and `osv-scanner --lockfile=<lockfile>` query online vulnerability databases and require approval; sub-agents mark `needs approval, not run`. `pip-audit` without flags audits the current Python environment rather than the project, and with `-r` creates a temp environment and installs packages—so always ask the user first
  - Whether lockfiles are committed; whether multiple package managers are mixed (scan §0)
- **Verdict**: Suspicious package → 🔴; high-severity vulnerability in runtime dependencies → 🟠; duplicate libraries for same role → 🟡/🟠; unused dependencies → 🟡.

### 5.5 ★ License Compliance
- **Check**: scan §8 (it only inspects JS dependency licenses; for manifests flagged `NOT checked`—Python, Rust, Go, etc.—check separately: run `pip-licenses` / `cargo license` / `go-licenses` read-only if installed, otherwise verify direct dependencies from the manifest one by one; never mark `pass` without checking); the project's own LICENSE; licenses of runtime dependencies and pasted open-source code (third-party directories listed in scan §0 and copied files—check file-header copyright notices).
  - **MIT / Apache-2.0 / BSD**: modifiable and commercially usable, but original copyright notices must be preserved (check for `THIRD_PARTY_NOTICES` or equivalent)
  - **GPL**: distributing derivative works requires open-sourcing under the same license
  - **AGPL**: serving over a network also triggers open-source obligations
  - **SSPL / BUSL / CC-BY-NC / Commons Clause**: non-OSS or restricts commercial use
- **Verdict**: GPL/AGPL/SSPL code in a closed-source or commercial project → 🔴 (send to user to decide: replace, isolate in a separate process, or open-source). Permissive licenses missing copyright notices → 🟡. If project stage or commercial intent is unclear, list in "Decisions Needed".
  - **Permissive open-source project + optional GPL component**: component is not in the repo, installed by the user, invoked as a separate process, and documented in NOTICES → pass; repo directly imports it → note "this part is governed by GPL when distributed together with the GPL component", ⚪.
  - **AI-generated assets** (TTS audio, generated images, model textures, voice references) bundled with the project: rights depend on the generator's plan terms (some free tiers forbid commercial use or require attribution). If provenance cannot be verified → list in "Decisions Needed", ⚪.

### 5.6 Reinventing the Wheel
- **Check**: Whether notoriously tricky core problems are hand-rolled from scratch despite mature libraries: timezones & dates, CSV/Excel parsing, rich text, audio/video codecs, cryptography, auth, drag-and-drop, virtualized lists. Conversely, whether built-in capabilities of the chosen framework (routing, state, forms, caching) are bypassed and reimplemented.
- **Verdict**: Hand-rolled implementation is also a bug hotspot (cross-check 6.8) → 🟠; otherwise 🟡. Counterintuitive code in mature open-source libraries usually guards against rare edge cases; hand-rolled versions step on every single one again.
