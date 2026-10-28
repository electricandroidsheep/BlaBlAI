# Contributing to BlaBlAI

Thank you for your interest in contributing to **BlaBlAI**! This project provides academic-grade AI documentation, claim verification, and tamper-evident auditing for university research.

---

## 🛠️ Development Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11, 3.12, 3.13, and 3.14 with Tcl/Tk 9.0)
- Windows, macOS, or Linux

### 2. Clone and Install Dependencies
```bash
git clone https://github.com/electricandroidsheep/BlaBlAI.git
cd BlaBlAI
pip install -r requirements.txt
pip install pyinstaller pytest
```

### 3. Launching the App
```bash
python app.py
```

---

## 🧪 Testing Guidelines

Before opening a pull request or submitting code changes, all 33 automated tests must pass without errors or warnings:

```bash
python -m unittest discover tests
```

### Writing New Tests
- Put new test methods in `tests/test_comprehensive.py`.
- Test both English (`en`) and German (`de`) locales if introducing UI strings or translation keys.
- If modifying PDF generation or document models, ensure APA booktabs formatting and SHA-256 tamper hashing remain fully intact.

---

## 📐 Design & Architecture Principles

1. **Academic Neutrality & Monochrome PDF Styling**:
   - PDF exports MUST adhere to APA / LaTeX Booktabs styling.
   - Do NOT introduce colored text or saturated backgrounds to the PDF generator. Headers, rules, and text are strictly black, white, and neutral grayscale tones.
2. **Pure Python Dependencies**:
   - The PDF generator is built on ReportLab 5. Do NOT introduce headless browser dependencies (e.g. Playwright, Selenium, Chromium) for PDF generation.
3. **Bilingual Symmetry (`i18n.py`)**:
   - Every string presented to the user must have an entry in both `TRANSLATIONS["en"]` and `TRANSLATIONS["de"]`.
   - Never hardcode raw strings in GUI views.
4. **Universal Scrolling (`gui/main_window.py`)**:
   - All scrolling is managed centrally via `MainWindow._on_touchpad_scroll` (Tcl/Tk 9.0 `<TouchpadScroll>` TIP 684) and `MainWindow._on_window_mousewheel` (`<MouseWheel>` / X11 buttons) using 3-tier container discovery (`_resolve_scroll_container`), nested textbox scroll pass-through, and `after_idle` burst coalescing. Do NOT bind ad-hoc `<MouseWheel>` handlers that trap scroll events on non-scrollable child widgets.
5. **Storage Compatibility**:
   - All `.ailog` JSON documents must maintain forward and backward compatibility. When adding fields to dataclasses in `models.py`, always provide sensible default values.

---

## 📦 Building Standalone Binaries

### Windows Standalone `.exe`
```powershell
.\build_exe.bat
# Or manually:
pyinstaller BlaBlAI.spec --clean --noconfirm
```
The output executable will be placed in `dist/BlaBlAI.exe`.

### macOS Application Bundle & `.dmg`
```bash
chmod +x build_mac.sh
./build_mac.sh
```
The output will be placed in `dist/BlaBlAI.app` and `dist/BlaBlAI.dmg`.

---

## 📄 License
By contributing to BlaBlAI, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
