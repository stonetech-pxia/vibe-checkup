# Dimension 1: Consistency & Single Source of Truth

**Guiding test**: For each concern (tokens, components, interactions, architecture), is there **one** authoritative source, and does the code actually use it?

---

### 1.1 ★ Single Source of Truth for Design Tokens
- **Check**:
  - Review scan §2 token file hints and `hardcoded_color` / `hardcoded_size`.
  - Count unique literal colors outside token files (for non-git repos, use `grep -rhoE … --exclude-dir=node_modules --exclude-dir=dist`):
    ```bash
    git grep -hoiE "#[0-9a-f]{6}\b|#[0-9a-f]{3}\b|rgba?\([^)]*\)" -- <src_dir> | tr A-F a-f | sort | uniq -c | sort -rn | head -40
    ```
  - Check whether spacing, border radius, font size, shadows, and animation durations come from one source (CSS vars, Tailwind theme, SwiftUI extensions, Theme object).
- **Verdict**:
  - 🟠: No token file; or token file exists but is widely bypassed (near-duplicate colors like `#333`/`#323232`/`#2f2f2f` signal active drift).
  - 🟡 or `pass`: Only isolated one-off literals (e.g., chart palette).

### 1.2 ★ Shared Component Reuse
- **Check**:
  - Locate the base component directory (`components/ui`, `common`, `shared`, `DesignSystem`, `Views/Components`).
  - Count implementations of Button / Input / Select / Modal (Dialog/Sheet/Popup) / Card / Toast / Tabs / Empty / Loading.
  - Grep for raw usages bypassing base components (e.g., `<button className=…>` despite `Button`, hand-rolled overlays despite `Sheet`).
- **Verdict**:
  - 🟠: ≥2 implementations for the same role (specify which one to keep—the most widely used and complete); or no base component layer with >5 **views containing UI controls** (windows, pages, panels; exclude pure render/animation/audio scripts).
  - **Merging**: With ≤2 control-bearing views where duplication is purely the same copied button/input styles from 1.1, report once under 1.1 (🟠) and mark 1.2 `see 1.1`. Report independent issues (e.g., duplicate `$`/`el` DOM helpers, multiple toast implementations) under 1.2.

### 1.3 ★ Consistent Interaction Patterns
- **Check**: Build a comparison table grouped by user intent, listing every occurrence and widget/pattern used:
  - Small-set single choice (card selector / dropdown / segmented control / radio)
  - Confirmation & destructive actions (double confirmation? undo?)
  - Loading states, empty states, error feedback (toast / inline / modal)
  - Form validation timing and submit-button disabled rules
  - Navigation & back behavior, keyboard shortcuts, drag-and-drop
- **Verdict**:
  - 🟠: ≥2 patterns for the same user intent without justification (include the comparison table).

### 1.4 Copy, Terminology & Internal Codenames
- **Check**:
  - Multiple names for the same concept across UI copy and code identifiers (e.g., project / workspace / work; export / output / render).
  - **Residual internal codenames**: author names or old project/product names in data model values (enums, roles, field values), env var prefixes, storage paths, or IDs.
  - If i18n is used, grep for user-visible hardcoded strings bypassing i18n.
- **Verdict**:
  - 🟠: Internal codenames in data models or validation logic; or multiple names for a core concept risking split models.
  - 🟡: Inconsistent UI copy only.

### 1.5 Multi-Device & Viewport Adaptation
- **Check**:
  - Inspect layout code of 2–3 main pages for fixed widths/heights, absolute positioning, hardcoded window sizes, and missing breakpoints / Dynamic Type / resize handling.
  - Static reads only: if live verification is needed, put target pages, viewports (`1366×768 @150%`, `1280×720`, 13" MacBook default, mobile `375×812`), and what to inspect in "Decisions Needed".
- **Verdict**:
  - 🟠: Core flow breaks at common viewports.
  - 🟡: Localized layout issues.

### 1.6 UI Specification Docs
- **Check**: Verify whether a design spec exists (colors, component inventory, interaction conventions), whether agent rule files link to it, and sample 3 tokens/components against code.
- **Verdict**:
  - 🟡: Has UI but no design spec (prescription: extract from current code as SSOT and link from `AGENTS.md`).
  - Doc contradicts code → grade under 3.2.

### 1.7 ★ Consistent Architectural Patterns (Applies to Non-UI Projects Too)
- **Check**: Check for coexisting solutions to the same concern:
  - State management (multiple stores / mixing Context with global singletons)
  - Network requests (scattered raw `fetch` + custom client + third-party library)
  - Styling approach (mixing CSS Modules + Tailwind + inline styles)
  - Dates, validation, logging, config loading, error types, persistence
  - Directory conventions (consistent placement across features)
- **Verdict**:
  - 🟠: Multiple coexisting approaches with no migration plan (prescription must choose the single keeper and provide an `AGENTS.md` rule).
