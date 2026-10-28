# Changelog

All notable changes to **BlaBlAI** are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-10-28

### Added
- **Global `<TouchpadScroll>` (Tcl/Tk 9.0 TIP 684) & `<MouseWheel>` Dispatch (`MainWindow`)**:
  - Full support for Tcl/Tk 9.0's `<TouchpadScroll>` event (used by Microsoft Surface Arc Mouse capacitive strips and Windows 11 Precision Touchpads in Python 3.14+), unpacking 32-bit packed `(deltaX, deltaY)` values per `::tk::PreciseScrollDeltas`.
  - 3-tier target container resolution: (1) hierarchy walk from `event.widget` (`%W`), (2) cursor coordinate hit-test via `winfo_containing`, and (3) direct active-view fallback (`scroll_docs`, `scroll_table`, `scroll_drops`, `form_scroll`).
  - Neutralizes CustomTkinter's legacy `_mouse_wheel_all` handler to prevent focus traps and dead-widget errors.
  - **Smooth Left-Pane Form Scrolling & Ghosting Mitigation**: Nested `CTkTextbox` widgets inside `LoggerView.form_scroll` (`txt_prompt`, `txt_output`, `txt_flaws`) pass scroll events smoothly to the parent form unless the textbox holds active keyboard focus and has vertical overflow. Added `after_idle` scroll burst coalescing, synchronous `canvas.update_idletasks()` redraw flushing, and 250ms hover-tooltip suppression during active scrolling.
- **Dedicated Interactive Verification Matrix Tab**:
  - Full CRUD support: fact-check entries can be added, edited inline via pre-populated form, and deleted.
  - Interaction linkage selector: assign claims to specific logged interactions (e.g. `Interaction #1 (Visplore Export)`) or keep them standalone.
  - Displays the interaction's short title directly beneath `Interaction #X` in both the GUI table and all exports.
- **Retroactive Time Logging & Custom DateTime Picker Dialog**:
  - Dedicated "Retroactive" toggle checkbox next to the interaction timestamp.
  - Interactive calendar date/time picker dialog (`gui/datetime_picker.py`) allowing quick historical interaction recording.
  - Automatic `(Retroactive)` labeling and `[Retroactive]` badge in card and protocol headers.
- **Always-Accessible Critical Reflection & Neutral `[N/A]` Decision**:
  - Removed collapsible toggle switch; reflection inputs are directly accessible and clearly marked as optional.
  - Introduced `"N/A"` as the default application decision alongside `"Accepted"`, `"Modified"`, and `"Rejected"`.
  - Added neutral gray `[N/A]` badges in interaction cards and protocols.
- **Pluralized Verification Source Headers**:
  - Updated English headers and labels to *"Verification Sources & Evidence"*.
  - Updated German headers and labels to *"Verifikationsquellen & Belege"*.
- **Comprehensive Test Suite Expansion**:
  - Added 13 new unit tests (33 total passing tests) covering `<TouchpadScroll>` unpacking, nested textbox scroll pass-through, short title formatting, N/A decision defaults, and plural header i18n.

### Changed
- Standardized action button color scheme: Edit buttons use solid primary blue (`#2b6cb0` / `#3182ce`), and Delete buttons use transparent background with red text and red outline (`#e53e3e`).
- Improved layout responsiveness: Set fixed minimum dimensions and disabled shrinkage on top-bar modal buttons (`User Profile`, `Language Switcher`).
- Upgraded Section B table column headers across Markdown, HTML, and ReportLab PDF renderers to reflect plural sources.
- Replaced remaining legacy `"drop"` terminology in user-facing empty-state strings (`i18n.py`) and documentation with `"interaction"` / `"Interaktion"`.

### Fixed
- Fixed issue on Windows 11 / Python 3.14 (Tcl/Tk 9.0) where high-precision scroll devices (Microsoft Surface Arc Mouse, Precision Touchpads) emitted `<TouchpadScroll>` instead of `<MouseWheel>`.
- Fixed severe scroll stalling on the left data-entry pane (`LoggerView.form_scroll`) when the mouse cursor passed over nested prompt/output/reflection `CTkTextbox` widgets.
- Reduced Win32 `tk.Canvas` scroll ghosting by coalescing high-frequency scroll bursts and flushing idle redraws (`update_idletasks()`) synchronously per frame.
- Fixed fact-check table rows not displaying interaction titles when linked.

---

## [1.0.0] - 2026-09-24

### Added
- **Welcome Hub & Profile Management**:
  - Modern BlaBlAI vector logo branding and uncluttered dashboard.
  - User profile modal storing student name, degree program, matriculation number, and custom bilingual AI affidavit statements.
  - Document cards with external author safeguard locks (`🔒 External Author`).
- **Interaction Drop Logger**:
  - Multi-engine interaction logging supporting major LLMs (Claude, Gemini, NotebookLM, ChatGPT, Perplexity, DeepSeek, Llama, Custom).
  - Smart raw output sanitizer automatically normalizing bullets, stripping code fences, and handling line wraps.
  - Support for artifact and non-text file references (images, charts, code scripts).
- **Tamper-Evident SHA-256 Audit Trail**:
  - Real-time cryptographic hashing over canonical interaction data.
  - Embedded audit digest and timestamp printed in both Markdown and PDF exports.
- **APA / LaTeX Booktabs PDF Generation**:
  - Pure-Python vector PDF engine built on ReportLab 5.
  - Strict grayscale/monochrome palette conforming to institutional examination guidelines.
  - Running header and footer containing student name and matriculation number across all pages.
- **Bilingual Interface**:
  - Comprehensive English and German locale support with instant runtime switching.
