# BlaBlAI
**Academic AI Interaction Protocol Logger & Exporter**
*Institution-Ready Generative AI Documentation, Verification & Tamper-Evident Auditing*

Tailored for **Sven Várszegi, B.A.** in the **Master Digital Business Management (FH OÖ / JKU)** program.

---

## 🎯 Purpose & Compliance
In European and Austrian higher education (including JKU Linz and FH Upper Austria), submitting coursework that utilized Generative Artificial Intelligence requires rigorous disclosure, prompt logging, critical reflection, and citation verification.

**BlaBlAI** provides an ergonomic, fully local desktop application to:
1. **Document interactions continuously** during thesis research, seminar writing, and coursework.
2. **Critically audit AI outputs** for plausibility, reasoning gaps, and bias.
3. **Execute adversarial fact-checking** against primary literature (DOIs, books, journals).
4. **Export tamper-evident protocols** to standard Markdown (`.md`) and publication-grade vector PDF (`.pdf`):
   - **Pure-Python Vector PDF Renderer:** Built on ReportLab 5 (zero headless browser or Chrome dependency).
   - **APA / LaTeX Booktabs Typography:** Monochrome table layout with thick top/bottom horizontal rules, thin midrules, no vertical lines, and pure white backgrounds.
   - **Cryptographic Tamper-Evidence:** Generates a canonical **SHA-256 integrity digest** embedded in the protocol header and dedicated *Verification & Audit Trail* block.
   - **Customizable Dual-Language Affidavits:** Editable English and German academic honor declarations.
   - **External Author Safeguard:** Read-only locks and visual badges prevent accidental overwrite when opening shared protocols.

---

## 🚀 Quick Start

### Option 1: Direct Run (Development / Portable Python)
Double-click `run.bat` or run in terminal:
```powershell
python app.py
```

### Option 2: Standalone Windows Executable (.exe)
Double-click `build_exe.bat` or run:
```powershell
pip install pyinstaller customtkinter markdown reportlab pillow
pyinstaller --noconsole --onefile --name "BlaBlAI" --add-data "styles.css;." --add-data "blablai_icon.png;." --collect-all customtkinter --collect-all reportlab --collect-all PIL app.py
```
This produces a single standalone file at `dist\BlaBlAI.exe`. It can be run on any Windows computer or copied to a USB stick with zero installation required!

### Option 3: Standalone macOS Bundle & .dmg Installer
On macOS, execute `build_mac.sh`:
```bash
chmod +x build_mac.sh
./build_mac.sh
```
This produces a native macOS application bundle (`dist/BlaBlAI.app`) and a drag-and-drop installer (`dist/BlaBlAI.dmg`). All user configuration is automatically stored in `~/Library/Application Support/BlaBlAI`.

---

## 📂 Core Features & Workflow

### 1. Welcome Hub ("Home")
- **Clean Vector Branding:** Modern BlaBlAI vector badge and clutter-free interface.
- **User Profile Modal:** Centrally customize your Student Name, Degree Program, Student ID / Matriculation Number, and custom English/German affidavit statements.
- **Document Cards:** Google Docs-style dashboard displaying course scope, drop count, modification date, and `🔒 External Author` badges for shared files.
- **Directory Routing:** Automatically routes files to `Documents/BlaBlAI_Protocols`.

### 2. Interaction Drop Logger
- **Timestamp & Model Memory:** Auto-CEST timestamp with `↺ Now` refresh. Presets use clean, unversioned family names (`Anthropic Claude`, `Google Gemini`, `Google NotebookLM`, `OpenAI ChatGPT`, `Perplexity AI`, `DeepSeek`, `Meta Llama`, `Custom...`) and remember your last-used engine.
- **Smart Output Sanitizer:** Pasting raw text or code automatically normalizes bullets, strips triple backticks, wraps runaway lines, and displays a friendly non-blocking feedback toast.
- **Artifact & Non-Text File References:** Submit prompts that generated images, videos, or notebooks (e.g. `Nanobanana`, `chart.png`, `script.py`) with a dedicated artifact file reference attached to the receipt.
- **Distinct Accent Textboxes:** Prompt input is framed with a cool blue border (`#3182ce`); Output is framed with a slate/teal border (`#38a169`).
- **Sticky Bottom Action Buttons:** Action buttons (`[+ Add Drop]`, `[Reset Form]`) stay firmly at the bottom of the form below all expandable toggles.
- **Interactive Tooltips:** Hover over any interactable (models, intent, prompt, toggles, language, theme) for contextual guidance.

### 3. Critical Reflection & Fact-Check Matrix
- **Plausibility Audit:** Log hallucinations, logic flaws, and assign an application decision (`[Accepted]`, `[Modified]`, `[Rejected]`).
- **Section B Fact-Checking:** Audit specific empirical claims against primary sources (`Confirmed`, `Refuted`, `Untestable`). All claims are compiled into the matrix.

### 4. Verification & Audit Trail (SHA-256 Tamper Detection)
- Every time a document is saved or exported, a canonical SHA-256 cryptographic hash is calculated over the document contents.
- Printed at the end of both PDF and Markdown exports alongside the audit timestamp and item counts to certify provenance.
- Academic metadata and running footers clearly display Student Name and Student ID (`Student: Name | ID: Matrikelnummer`) across every page.

---

## 🧪 Comprehensive Automated Test Suite
Run the 20 automated tests:
```powershell
python -m unittest discover tests
```
Verifies i18n symmetry, formatting placeholders, special character encoding, macOS/Windows POSIX paths, SHA-256 tamper sensitivity, Student ID in footers, output artifact references, auto-cleaning, and ReportLab APA PDF vector rendering.
