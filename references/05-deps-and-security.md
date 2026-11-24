# Dimension 5: Dependencies, Licenses & Security

Redact secrets everywhere per `agent-brief.md` Discipline #4.

---

### 5.1 ★ Secrets & Credentials
- **Check**:
  - Review scan §3.
  - Verify `.env` is ignored: `git check-ignore -v .env`.
  - Check git history (list commits only; open matches to distinguish real-length keys from placeholders or prefix-detection code):
    ```bash
    git log --all -S "<suspicious_prefix>" --format="%h %ad %s"
    ```
  - Server-side secrets leaked to clients: `NEXT_PUBLIC_*` / `VITE_*` / `EXPO_PUBLIC_*` containing `SECRET`/`KEY`/`TOKEN`; API keys bundled into Electron renderers, mobile builds, or browser extensions.
- **Verdict**:
  - 🔴: Real secret in code or git history (prescription: revoke & rotate first, then scrub); or server-side secret exposed to client.

### 5.2 ★ Authentication & Authorization
- **Check**: Auth enforcement on every backend route / cloud function; frontend-only auth; ownership checks on ID lookups (IDOR); Supabase RLS / Firebase rules (`if true`); exposed admin/debug endpoints.
- **Verdict (general)**:
  - 🔴: Auth/authz gap involving real user data.
  - 🟠: Same gap in `prototype` stage (note `must fix before launch`).
- **Desktop local endpoints** (local WebSocket/HTTP, IPC):
  - 🔴: Binds to `0.0.0.0`.
  - 🟠: Missing strict `127.0.0.1` binding or `Origin` header rejection.
  - 🟡: Baseline present but no auth token protecting sensitive local data (screenshots, transcripts, files).
- **Metered / paid endpoints** (LLM, SMS, email, pay-per-use API proxies; retry/polling/agent loops):
  - 🔴: Unauthenticated paid endpoint with external users (`🟠` with `must fix before launch` otherwise).
  - 🟡: Authenticated without per-user/IP rate limiting, or unbounded retry/polling/agent loops.

### 5.3 Injection, Dangerous APIs, Misconfiguration & Privacy
- **Check**:
  - **Injection**: SQL concatenation; `eval` / `exec` / `new Function`; `dangerouslySetInnerHTML` / `v-html` / `innerHTML` with user input; unescaped shell interpolation; unnormalized file paths; SSRF.
  - **Electron**: `nodeIntegration: true`, `contextIsolation: false`, `webSecurity: false`.
  - **Desktop shell only** (`BrowserWindow` / `preload` / `ipcMain` / `tauri.conf`; skip sub-check otherwise): does `preload` allowlist IPC channel names instead of unrestricted `send`/`on`? Are `setWindowOpenHandler` and `will-navigate` guards in place? Do windows load only local content?
  - **Config**: `*` CORS with credentials; debug mode in prod; raw stack traces returned to clients; default passwords; publicly writable storage buckets.
  - **Privacy**: PII, tokens, or full request bodies in logs; unconsented telemetry; sensitive data stored locally in plaintext.
- **Verdict**:
  - 🔴 / 🟠: Reachable by user input or involving real user data; desktop shell loading external/user content without IPC/navigation guards (🟠).
  - 🟡: Trusted internal input only or `prototype` stage.
  - ⚪: Generic desktop IPC bridge loading local content only.

### 5.4 ★ Dependency Health
- **Check**:
  - Dependency count (scan §0) and duplicate libraries for the same role (`axios` + `ky` + custom `fetch`; `moment` + `dayjs`; two UI libs)—if same root cause as 1.7, score once.
  - Unused deps (**only if installed**): `npx --no-install depcheck` or `npx --no-install knip`.
  - **Hallucinated / typosquatted packages**: verify unfamiliar names (especially 1–2 chars off popular packages) via read-only `npm view <pkg> name version` or `pip index versions <pkg>`.
  - **Known vulnerabilities** (network/install—require user approval; sub-agents mark `needs approval, not run`): `npm audit --omit=dev`, `osv-scanner --lockfile=<lockfile>`, `pip-audit` (always ask: without flags it audits the ambient env; with `-r` it installs packages).
  - Lockfiles committed; mixed package managers (scan §0).
- **Verdict**:
  - 🔴: Suspicious/hallucinated package.
  - 🟠: High-severity vulnerability in runtime deps; severe duplicate libraries.
  - 🟡: Duplicate libraries; unused dependencies.

### 5.5 ★ License Compliance
- **Check**:
  - Review scan §8 (JS deps + in-repo `LICENSE` files). For manifests marked `NOT checked` (Python, Rust, Go, etc.), run `pip-licenses` / `cargo license` / `go-licenses` read-only if installed, or check direct manifest deps individually—never mark `pass` without checking.
  - Check project's own LICENSE, runtime deps, and pasted third-party code headers (scan §0 third-party dirs).
  - License tiers:
    - **MIT / Apache-2.0 / BSD**: commercially usable; preserve copyright notices (`THIRD_PARTY_NOTICES` or equivalent)
    - **GPL**: derivative distribution requires same-license open-sourcing
    - **AGPL**: network serving triggers open-source obligation
    - **SSPL / BUSL / CC-BY-NC / Commons Clause**: non-OSS or restricts commercial use
- **Verdict**:
  - 🔴: GPL/AGPL/SSPL code in a closed-source or commercial project (list options for user: replace, isolate in separate process, or open-source).
  - 🟡: Permissive licenses missing copyright notices.
  - **Permissive OSS + optional GPL component**: external user-installed separate process documented in NOTICES → `pass`; directly imported → ⚪ (note governed by GPL when distributed together).
  - **Bundled AI-generated assets** (TTS audio, images, textures, voice refs): if commercial rights/provenance cannot be verified → ⚪ + "Decisions Needed".
  - Unclear stage or commercial intent → list in "Decisions Needed".

### 5.6 Reinventing the Wheel
- **Check**: Hand-rolled complex domains despite mature libraries (timezones/dates, CSV/Excel, rich text, audio/video codecs, crypto, auth, drag-and-drop, virtualized lists), or bypassing framework built-ins (routing, state, forms, caching).
- **Verdict**:
  - 🟠: Hand-rolled implementation is also a bug hotspot (cross-check 6.8).
  - 🟡: Otherwise.
