# Dimension 1: Consistency & Single Source of Truth

**Root cause**: When AI builds a new feature without seeing the whole repo, it invents a local set of styles, a new component, and a new interaction pattern on the spot. Each feature "works" in isolation, yet together the product lacks cohesion—and the next agent has no idea which pattern to follow, so it picks one at random or invents pattern #N.

**Guiding test**: For each category (colors, spacing, buttons, single-choice inputs, modals, request layers…), is there **one** authoritative source, and does the code actually use it?

---

### 1.1 ★ Single Source of Truth for Design Tokens
- **Check**: scan §2's token file hints and `hardcoded_color` / `hardcoded_size`. Count unique literal colors outside token files (`git grep` automatically skips git-ignored directories like `node_modules`; for non-git projects use `grep -rhoE … --exclude-dir=node_modules --exclude-dir=dist`):
  `git grep -hoiE "#[0-9a-f]{6}\b|#[0-9a-f]{3}\b|rgba?\([^)]*\)" -- <src_dir> | tr A-F a-f | sort | uniq -c | sort -rn | head -40` (include `rgba`: semi-transparent colors drift the fastest).
  Also check whether spacing, border radius, font size, shadows, and animation durations come from a single source (CSS variables, Tailwind theme, SwiftUI extensions, Theme object).
- **Verdict**: No token file → 🟠. Token file exists but is widely bypassed → 🟠. Near-duplicate colors (`#333` / `#323232` / `#2f2f2f`) indicate drift is already underway. Only a few isolated one-off literals (e.g., chart palette) → 🟡 or pass.

### 1.2 ★ Shared Component Reuse
- **Check**: Locate the base component directory (`components/ui`, `common`, `shared`, `DesignSystem`, `Views/Components`). List how many implementations exist for Button / Input / Select / Modal (Dialog/Sheet/Popup) / Card / Toast / Tabs / Empty / Loading. Then grep for raw usages bypassing base components (e.g., `<button className=…>` despite having a `Button` component; hand-rolled overlays despite having a shared `Sheet`).
- **Verdict**: ≥2 implementations for the same role → 🟠, and specify which one to keep (the most widely used and complete one). No base component layer while the project has more than 5 **views containing UI controls** (windows, pages, panels) → 🟠; scripts for rendering, animation, or audio that produce no controls do not count as views.
- **Merging**: When there are very few control-bearing views (≤2) and the duplication is actually the same batch of styles from 1.1 (two windows copying the same button/input styles), the root cause is identical—report one finding under 1.1 (still 🟠) and mark 1.2 `see 1.1`. If independent issues remain (e.g., duplicate `$`/`el` DOM helpers, multiple toast implementations), report them under 1.2 at their actual severity.

### 1.3 ★ Consistent Interaction Patterns
- **Check**: Build a comparison table grouped by "same user intent", listing every occurrence and the widget/pattern used:
  - Small-set single choice (card selector / dropdown / segmented control / radio)
  - Confirmation & destructive actions (double confirmation? undo?)
  - Loading states, empty states, error feedback (toast / inline / modal)
  - Form validation timing and submit-button disabled rules
  - Navigation & back behavior, keyboard shortcuts, drag-and-drop
- **Verdict**: Two or more patterns for the same user intent with no justification → 🟠 (include the comparison table). Users immediately feel this as "unpolished".

### 1.4 Copy, Terminology & Internal Codenames
- **Check**:
  - Whether the same concept has multiple names across UI copy and code identifiers (e.g., project / workspace / work; export / output / render)
  - **Residual internal codenames**: author names, old project names, or old product names inside data model values (enums, roles, field values), env var prefixes, storage directories, or IDs—very common after a vibe-coded project is split out of another repo or renamed
  - If the project uses i18n, grep for user-visible hardcoded strings bypassing i18n
- **Verdict**: Internal codenames baked into data models or validation logic (one typo causes silent rejection) → 🟠; multiple names for a core concept that could cause an agent to build two separate models → 🟠; inconsistent UI copy only → 🟡.

### 1.5 Multi-Device & Viewport Adaptation
- **Check**: Fixed widths/heights, absolute positioning, hardcoded window sizes, missing breakpoints / Dynamic Type / window resize handling. Read layout code for 2–3 main pages. Checkups are static reads only; if launching the app is needed for live verification, put "which page to open, what sizes to test, and what to look for" into "Decisions Needed" for the user to run. Common test viewports: desktop 1366×768 at 150% scaling, 1280×720, 13-inch MacBook default resolution; mobile 375×812.
- **Verdict**: Core flow breaks at other common sizes → 🟠; localized issues → 🟡.

### 1.6 UI Specification Docs
- **Check**: Whether a design spec exists (colors, component inventory, interaction conventions) and whether agent rule files point to it. Sample 3 tokens/components from the doc and verify they match the code.
- **Verdict**: Has UI but no doc → 🟡 (prescription: extract one from current code as the single source of truth and link to it from `AGENTS.md`). Doc contradicts code → handle under 3.2 (misleading docs can be 🔴).

### 1.7 ★ Consistent Architectural Patterns (Applies to Non-UI Projects Too)
- **Check**: Whether multiple solutions coexist for the same concern:
  - State management (two stores / mixing Context with global singletons)
  - Network requests (scattered raw `fetch` + custom client + third-party library)
  - Styling approach (mixing CSS Modules + Tailwind + inline styles)
  - Dates, validation, logging, config loading, error types, persistence
  - Directory conventions: where should a new feature live? Do existing features follow the same rule?
- **Verdict**: Multiple coexisting approaches with no migration plan → 🟠. The prescription must pick the single one to keep and provide a rule to add to `AGENTS.md`.
