"""
Protocol generator and exporter.
Compiles ProtocolDocument into standard dual-language Markdown and renders
publication-ready vector PDFs directly via pure-Python ReportLab engine
(zero browser dependency) with optional browser fallback.
"""

from __future__ import annotations
import os
import sys
import subprocess
import tempfile
import html
from pathlib import Path
from typing import Optional, List

from models import ProtocolDocument, ProtocolMetadata, InteractionDrop, FactCheckEntry

# Dual-language academic integrity declaration
AI_USE_STATEMENT_EN = (
    "I hereby declare that this academic work was conducted in accordance with institutional "
    "guidelines on generative artificial intelligence. AI systems were utilized as auxiliary tools "
    "for synthesis, method checking, and ideation under rigorous human oversight. All factual claims, "
    "citations, and analytical arguments generated with AI assistance have been independently audited "
    "and verified against primary academic literature. I assume full intellectual responsibility "
    "for the entirety of the submitted work."
)

AI_USE_STATEMENT_DE = (
    "Hiermit erkläre ich, dass die vorliegende wissenschaftliche Arbeit unter Einhaltung der "
    "hochschulspezifischen Richtlinien zum Einsatz generativer Künstlicher Intelligenz verfasst wurde. "
    "KI-Systeme wurden ausschließlich als unterstützende Hilfsmittel unter kontinuierlicher menschlicher "
    "Kontrolle eingesetzt. Sämtliche durch KI generierten Fakten, Zitate und Argumente wurden anhand "
    "wissenschaftlicher Primärquellen eigenständig überprüft. Die wissenschaftliche und inhaltliche "
    "Gesamtverantwortung verbleibt uneingeschränkt bei der Verfasserin bzw. dem Verfasser."
)


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller frozen exe."""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path


def clean_raw_interaction_text(text: str) -> str:
    """
    Cleans and normalizes pasted AI text for clean presentation.
    - Strips outer redundant markdown code fences (```text / ```)
    - Normalizes bullet points (•, ▪, ▫, * -> -)
    - Collapses excessive consecutive newlines (>2 down to 2)
    - Converts tabs to 4 spaces
    """
    if not text:
        return ""

    import re
    text = text.replace("\t", "    ")

    # Strip accidental outer code fences if user copied an entire response with ```
    lines = text.strip().splitlines()
    if len(lines) >= 2:
        first = lines[0].strip()
        last = lines[-1].strip()
        if (first.startswith("```") or first.startswith("~~~")) and (last.startswith("```") or last.startswith("~~~")):
            lines = lines[1:-1]

    # Normalize bullet points line-by-line
    norm_lines = []
    for line in lines:
        norm_line = re.sub(r'^[ \t]*[•▪▫\*]\s*', '- ', line)
        norm_lines.append(norm_line)

    text = "\n".join(norm_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def wrap_long_code_lines(text: str, max_len: int = 86) -> str:
    """Wraps exceptionally long lines (e.g. uninterrupted URLs or long hashes) to prevent margin clipping."""
    out_lines = []
    for line in text.splitlines():
        if len(line) > max_len and " " not in line.strip():
            chunks = [line[i:i + max_len] for i in range(0, len(line), max_len)]
            out_lines.append("\n".join(chunks))
        else:
            out_lines.append(line)
    return "\n".join(out_lines)


def generate_markdown(doc: ProtocolDocument) -> str:
    """Compiles the ProtocolDocument into publication-standard bilingual Markdown."""
    doc.renumber_drops()
    doc.compute_integrity_hash()
    meta = doc.metadata

    models_used = doc.get_all_models_used()
    aff_en = (meta.affidavit_en or "").strip() or AI_USE_STATEMENT_EN
    aff_de = (meta.affidavit_de or "").strip() or AI_USE_STATEMENT_DE

    lines: List[str] = [
        "# Generative AI Documentation & Verification Protocol",
        "## Anhang: Dokumentation und Verifikationsprotokoll",
        "",
        "### Academic AI Use Declaration / Erklärung zur Verwendung generativer KI",
        "",
        f"> **English:** {aff_en}",
        "",
        f"> **Deutsch:** {aff_de}",
        "",
        "---",
        "",
        "### Academic Metadata / Akademische Metadaten",
        "",
        "| Attribute / Attribut | Specification / Angabe |",
        "| :--- | :--- |",
        f"| **Student Name / Name d. Studierenden** | {meta.student_name} |",
        f"| **Student ID / Matrikelnummer** | {meta.matriculation_number.strip() if meta.matriculation_number else 'N/A'} |",
        f"| **Degree Program / Studiengang** | {meta.degree_program} |",
        f"| **Course Code & Title / Lehrveranstaltung** | {meta.course_code_title or 'N/A'} |",
        f"| **Assignment Scope / Umfang der Arbeit** | {meta.assignment_scope or 'N/A'} |",
        f"| **Examiner / Supervisor / Betreuung** | {meta.examiner or 'N/A'} |",
        f"| **Submission Date / Abgabedatum** | {meta.submission_date} |",
        f"| **AI Models Utilized / Verwendete KI-Modelle** | {models_used} |",
        "",
        "---",
        "",
        "### Section A: Chronological Interaction Protocol",
        "#### Abschnitt A: Chronologisches Interaktionsprotokoll",
        "",
    ]

    if not doc.drops:
        lines.append("*No interaction drops recorded in this session / Keine Interaktions-Drops erfasst.*")
        lines.append("")
    else:
        for drop in doc.drops:
            decision = (
                drop.critical_examination.application_decision
                if drop.critical_examination
                else "Accepted"
            )
            scope = drop.context_scope.strip() if drop.context_scope else "General / Zero Context"
            clean_prompt = clean_raw_interaction_text(drop.raw_prompt) or "[No prompt provided / Kein Prompt erfasst]"
            clean_output = clean_raw_interaction_text(drop.raw_output) or "[No output provided / Keine KI-Antwort erfasst]"

            prompt_fence = "````text\n" if "```" in clean_prompt else "```text\n"
            prompt_end = "\n````" if "```" in clean_prompt else "\n```"

            output_fence = "````text\n" if "```" in clean_output else "```text\n"
            output_end = "\n````" if "```" in clean_output else "\n```"

            lines.extend([
                f"#### Drop #{drop.drop_number}: {drop.core_intent} — {drop.target_engine} ({drop.timestamp})",
                f"- **Context Scope / Kontextbereich:** `{scope}`",
                f"- **Application Decision / Übernahmeentscheidung:** **[{decision}]**",
                "",
                "**Raw Prompt / Ursprünglicher Prompt:**",
                f"{prompt_fence}{clean_prompt}{prompt_end}",
                "",
                "**Raw AI Output / Ursprüngliche KI-Antwort:**",
                f"{output_fence}{clean_output}{output_end}",
                "",
            ])

            if drop.output_file_reference and drop.output_file_reference.strip():
                lines.extend([
                    f"📎 **Generated Artifact Reference / Generierte Dateireferenz:** <u>**{drop.output_file_reference.strip()}**</u> *(see accompanying submission files / siehe Einreichungsdateien)*",
                    "",
                ])

            if drop.critical_examination and drop.critical_examination.flaws_plausibility.strip():
                lines.extend([
                    "**Critical Examination & Plausibility Audit / Kritische Prüfung & Plausibilitätsaudit:**",
                    f"> {drop.critical_examination.flaws_plausibility.strip()}",
                    "",
                ])
            lines.append("---")
            lines.append("")

    # Section B: Fact-Checking Matrix
    lines.extend([
        "### Section B: Adversarial Fact-Checking Matrix",
        "#### Abschnitt B: Matrix zur adversarialen Faktenprüfung",
        "",
    ])

    all_facts = doc.get_all_fact_checks()
    if not all_facts:
        lines.append("*No adversarial fact-check claims recorded / Keine adversarialen Faktenprüfungen erfasst.*")
        lines.append("")
    else:
        lines.extend([
            "| Ref / Nr. | Claim / Extrahierte Aussage | Primary Source Citation / Primärquelle | Status | Rectification / Audit Note / Prüfvermerk |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for fc in all_facts:
            claim = fc.claim.replace("|", "\\|").replace("\n", " ").strip()
            source = fc.primary_source.replace("|", "\\|").replace("\n", " ").strip() or "N/A"
            note = fc.rectification_note.replace("|", "\\|").replace("\n", " ").strip() or "None / Keine"
            status_badge = f"**[{fc.status}]**"
            ref = fc.drop_reference or "General"
            lines.append(f"| **{ref}** | {claim} | {source} | {status_badge} | {note} |")
        lines.append("")

    # Section C: Verification & Audit Trail (Tamper-Evidence)
    lines.extend([
        "---",
        "",
        "### Section C: Verification & Audit Trail",
        "#### Abschnitt C: Verifikation & Prüfpfad",
        f"- **Document Integrity Hash / Dokument-Prüfsumme (SHA-256):** `{doc.integrity_hash}`",
        f"- **Audit Timestamp / Zeitstempel (CEST):** `{doc.hash_timestamp}`",
        f"- **Total Interaction Drops Logged / Protokollierte Interaktionen:** `{len(doc.drops)}`",
        f"- **Total Audited Fact-Checks / Geprüfte Fakten:** `{len(all_facts)}`",
        "- **Authenticity Notice / Authentizitätshinweis:** *This cryptographic SHA-256 digest certifies the authenticity and integrity of this protocol at the time of export. Any subsequent manual alteration of recorded interactions invalidates this signature. / Diese kryptographische SHA-256-Prüfsumme bescheinigt die Authentizität und Unverfälschtheit dieses Protokolls zum Zeitpunkt des Exports. Jede nachträgliche manuelle Bearbeitung macht diese Signatur ungültig.*",
        "",
    ])

    return "\n".join(lines)


# ==============================================================================
# Pure-Python Native ReportLab PDF Renderer (Zero Browser Dependency)
# ==============================================================================

_FONTS_REGISTERED = False
_REGISTERED_MONO = "Courier"
_REGISTERED_MONO_BOLD = "Courier-Bold"
_REGISTERED_SANS = "Helvetica"
_REGISTERED_SANS_BOLD = "Helvetica-Bold"
_HAS_TTFONTS = False


def ensure_system_fonts_registered():
    """Dynamically registers system TrueType fonts (Consolas/Arial on Windows, Menlo/Arial on macOS) for full Unicode support."""
    global _FONTS_REGISTERED, _REGISTERED_MONO, _REGISTERED_MONO_BOLD, _REGISTERED_SANS, _REGISTERED_SANS_BOLD, _HAS_TTFONTS
    if _FONTS_REGISTERED:
        return _REGISTERED_MONO, _REGISTERED_MONO_BOLD, _REGISTERED_SANS, _REGISTERED_SANS_BOLD, _HAS_TTFONTS

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", "C:\\Windows")
        fdir = Path(windir) / "Fonts"
        consola = fdir / "consola.ttf"
        consolab = fdir / "consolab.ttf"
        arial = fdir / "arial.ttf"
        arialbd = fdir / "arialbd.ttf"

        if consola.exists():
            try:
                pdfmetrics.registerFont(TTFont("Consolas", str(consola)))
                _REGISTERED_MONO = "Consolas"
                _HAS_TTFONTS = True
                if consolab.exists():
                    pdfmetrics.registerFont(TTFont("Consolas-Bold", str(consolab)))
                    _REGISTERED_MONO_BOLD = "Consolas-Bold"
                else:
                    _REGISTERED_MONO_BOLD = "Consolas"
            except Exception:
                pass

        if arial.exists():
            try:
                pdfmetrics.registerFont(TTFont("Arial", str(arial)))
                _REGISTERED_SANS = "Arial"
                if arialbd.exists():
                    pdfmetrics.registerFont(TTFont("Arial-Bold", str(arialbd)))
                    _REGISTERED_SANS_BOLD = "Arial-Bold"
                else:
                    _REGISTERED_SANS_BOLD = "Arial"
            except Exception:
                pass

    elif sys.platform == "darwin":
        mono_candidates = [
            Path("/System/Library/Fonts/SFNSMono.ttf"),
            Path("/Library/Fonts/Courier New.ttf"),
            Path("/System/Library/Fonts/Monaco.ttf"),
        ]
        sans_candidates = [
            Path("/Library/Fonts/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/Library/Fonts/Helvetica.ttf"),
        ]
        for mc in mono_candidates:
            if mc.exists():
                try:
                    pdfmetrics.registerFont(TTFont("MacMono", str(mc)))
                    _REGISTERED_MONO = "MacMono"
                    _REGISTERED_MONO_BOLD = "MacMono"
                    _HAS_TTFONTS = True
                    break
                except Exception:
                    pass
        for sc in sans_candidates:
            if sc.exists():
                try:
                    pdfmetrics.registerFont(TTFont("MacSans", str(sc)))
                    _REGISTERED_SANS = "MacSans"
                    _REGISTERED_SANS_BOLD = "MacSans"
                    break
                except Exception:
                    pass

    _FONTS_REGISTERED = True
    return _REGISTERED_MONO, _REGISTERED_MONO_BOLD, _REGISTERED_SANS, _REGISTERED_SANS_BOLD, _HAS_TTFONTS


UNICODE_TRANSLITERATIONS = {
    # Box drawing
    "│": "|", "┃": "|", "┆": "|", "┊": "|",
    "─": "-", "━": "-", "┄": "-", "┈": "-",
    "┌": "+", "┍": "+", "┎": "+", "┏": "+",
    "┐": "+", "┑": "+", "┒": "+", "┓": "+",
    "└": "+", "┕": "+", "┖": "+", "┗": "+",
    "┘": "+", "┙": "+", "┚": "+", "┛": "+",
    "├": "+", "┝": "+", "┞": "+", "┟": "+", "┠": "+", "┡": "+", "┢": "+", "┣": "+",
    "┤": "+", "┥": "+", "┦": "+", "┧": "+", "┨": "+", "┩": "+", "┪": "+", "┫": "+",
    "┬": "+", "┭": "+", "┮": "+", "┯": "+", "┰": "+", "┱": "+", "┲": "+", "┳": "+",
    "┴": "+", "┵": "+", "┶": "+", "┷": "+", "┸": "+", "┹": "+", "┺": "+", "┻": "+",
    "┼": "+", "┽": "+", "┾": "+", "┿": "+", "╀": "+", "╁": "+", "╂": "+", "╃": "+",
    # Arrows / pointers
    "►": ">", "◄": "<", "▼": "v", "▲": "^",
    "→": "->", "←": "<-", "⇒": "=>", "⇐": "<=", "⇔": "<=>",
    # Quotes / dashes / dots
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
    "‘": "'", "’": "'", "‚": "'",
    "—": "--", "–": "-", "…": "...",
    # Symbols
    "•": "*", "·": "*", "✔": "[v]", "✓": "[v]", "✖": "[x]", "✗": "[x]",
}


def sanitize_text_for_pdf(text: str, is_ttfont: bool = True) -> str:
    """Safely sanitizes text so non-standard characters never crash font encoders."""
    if not text:
        return ""
    if not is_ttfont:
        for char, repl in UNICODE_TRANSLITERATIONS.items():
            text = text.replace(char, repl)
        text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text


class NumberedCanvas:
    """Canvas wrapper that records pages and draws dynamic headers and running page numbers in monochrome."""
    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def create_factory(cls, student_name: str, doc_title: str, font_name: str = "Helvetica", student_id: str = ""):
        from reportlab.pdfgen import canvas

        class CustomNumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                num_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self.draw_page_decorations(num_pages)
                    super().showPage()
                super().save()

            def draw_page_decorations(self, page_count: int):
                from reportlab.lib.colors import HexColor
                self.saveState()
                self.setFont(font_name, 8)
                self.setFillColor(HexColor("#4B5563"))

                # Top Running Header (from page 2 onwards) - Pure Monochrome
                if self._pageNumber > 1:
                    clean_title = sanitize_text_for_pdf(doc_title, is_ttfont=True)
                    self.drawString(45, 805, f"{clean_title} — AI Interaction Protocol / KI-Protokoll")
                    self.setStrokeColor(HexColor("#CBD5E0"))
                    self.setLineWidth(0.5)
                    self.line(45, 798, 550, 798)

                # Bottom Footer (all pages) - Pure Monochrome with Student ID
                clean_name = sanitize_text_for_pdf(student_name, is_ttfont=True)
                if student_id and str(student_id).strip():
                    clean_id = sanitize_text_for_pdf(str(student_id).strip(), is_ttfont=True)
                    footer_text = f"Student: {clean_name} | ID: {clean_id}"
                else:
                    footer_text = f"Student: {clean_name}"
                page_str = f"Page {self._pageNumber} of {page_count} / Seite {self._pageNumber} von {page_count}"
                self.drawString(45, 32, footer_text)
                self.drawRightString(550, 32, page_str)
                self.setStrokeColor(HexColor("#CBD5E0"))
                self.setLineWidth(0.5)
                self.line(45, 42, 550, 42)

                self.restoreState()

        return CustomNumberedCanvas


def format_code_paragraph(text: str, style, is_ttfont: bool = True) -> Paragraph:
    """Safely escapes text and formats newlines for a flowing monospaced codeblock Paragraph."""
    from reportlab.platypus import Paragraph
    cleaned = clean_raw_interaction_text(text)
    if not cleaned:
        return Paragraph("<font color='#6B7280'><i>[No content recorded / Keine Inhalte erfasst]</i></font>", style)

    cleaned = wrap_long_code_lines(cleaned)
    cleaned = sanitize_text_for_pdf(cleaned, is_ttfont=is_ttfont)
    clean = html.escape(cleaned)
    clean = clean.replace("\n", "<br/>").replace("  ", "&nbsp;&nbsp;")
    return Paragraph(clean, style)


def render_to_pdf_reportlab(doc: ProtocolDocument, output_pdf_path: str) -> str:
    """
    Renders ProtocolDocument to publication-ready vector PDF using ReportLab.
    100% self-contained in pure Python with zero external browser dependencies.
    Strictly academic monochrome/grayscale design with perfect margin alignment.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        KeepTogether,
        HRFlowable,
    )

    doc.renumber_drops()
    meta = doc.metadata

    out_path = Path(output_pdf_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Register system fonts for full Unicode & Consolas/Arial rendering
    font_mono, font_mono_bold, font_sans, font_sans_bold, has_ttfonts = ensure_system_fonts_registered()

    # Document margins: 45pt left/right (~16mm), 52pt top/bottom (~18mm)
    pdf_doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=45,
        rightMargin=45,
        topMargin=52,
        bottomMargin=52,
    )

    # Styles - Strictly Monochrome / Grayscale (Blacks, Whites, Grays)
    base_styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "DocTitle",
        parent=base_styles["Heading1"],
        fontName=font_sans_bold,
        fontSize=17,
        leading=21,
        textColor=colors.HexColor("#111827"),
        spaceAfter=3,
    )

    style_subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=base_styles["Heading2"],
        fontName=font_sans,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=10,
    )

    style_h3 = ParagraphStyle(
        "SectionH3",
        parent=base_styles["Heading3"],
        fontName=font_sans_bold,
        fontSize=11.5,
        leading=15.5,
        textColor=colors.HexColor("#111827"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    style_body = ParagraphStyle(
        "DocBody",
        parent=base_styles["Normal"],
        fontName=font_sans,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1F2937"),
    )

    style_decl_title = ParagraphStyle(
        "DeclTitle",
        parent=base_styles["Normal"],
        fontName=font_sans_bold,
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor("#111827"),
        spaceAfter=2,
    )

    style_decl_body = ParagraphStyle(
        "DeclBody",
        parent=base_styles["Normal"],
        fontName=font_sans,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6,
    )

    style_table_key = ParagraphStyle(
        "TableKey",
        parent=base_styles["Normal"],
        fontName=font_sans_bold,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#374151"),
    )

    style_table_val = ParagraphStyle(
        "TableVal",
        parent=base_styles["Normal"],
        fontName=font_sans,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#111827"),
    )

    style_code_label = ParagraphStyle(
        "CodeLabel",
        parent=base_styles["Normal"],
        fontName=font_sans_bold,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#111827"),
        spaceBefore=8,
        spaceAfter=2,
        keepWithNext=True,
    )

    # Fixed code block padding: leftIndent=bp and rightIndent=bp ensure the box starts
    # exactly at the left margin (45pt) and ends exactly at the right margin (550pt).
    # spaceBefore=12 guarantees zero overlap with the label above.
    bp = 6
    style_code_prompt = ParagraphStyle(
        "CodePromptBlock",
        parent=base_styles["Code"],
        fontName=font_mono,
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#111827"),
        backColor=colors.HexColor("#F8FAFC"),
        borderColor=colors.HexColor("#CBD5E1"),
        borderWidth=0.75,
        borderPadding=bp,
        leftIndent=bp,
        rightIndent=bp,
        borderRadius=2,
        spaceBefore=12,
        spaceAfter=8,
    )

    style_code_output = ParagraphStyle(
        "CodeOutputBlock",
        parent=base_styles["Code"],
        fontName=font_mono,
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#111827"),
        backColor=colors.HexColor("#F8FAFC"),
        borderColor=colors.HexColor("#4B5563"),
        borderWidth=0.75,
        borderPadding=bp,
        leftIndent=bp,
        rightIndent=bp,
        borderRadius=2,
        spaceBefore=12,
        spaceAfter=8,
    )

    # Monochrome critical reflection block
    style_critical = ParagraphStyle(
        "CritText",
        parent=base_styles["Normal"],
        fontName=font_sans,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#111827"),
        backColor=colors.HexColor("#F8FAFC"),
        borderColor=colors.HexColor("#4B5563"),
        borderWidth=0.75,
        borderPadding=bp,
        leftIndent=bp,
        rightIndent=bp,
        borderRadius=2,
        spaceBefore=10,
        spaceAfter=8,
    )

    story = []

    # 1. Document Title & Subtitle - Pure Monochrome
    story.append(Paragraph("Generative AI Documentation &amp; Verification Protocol", style_title))
    story.append(Paragraph("Anhang: Dokumentation und Verifikationsprotokoll", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#111827"), spaceAfter=10))

    # 2. Dual-Language AI Use Declaration Box - Monochrome
    aff_en = (meta.affidavit_en or "").strip() or AI_USE_STATEMENT_EN
    aff_de = (meta.affidavit_de or "").strip() or AI_USE_STATEMENT_DE

    decl_data = [
        [
            Paragraph("Academic AI Use Declaration (English)", style_decl_title),
        ],
        [
            Paragraph(sanitize_text_for_pdf(aff_en, is_ttfont=has_ttfonts), style_decl_body),
        ],
        [
            Paragraph("Erklärung zur Verwendung generativer KI (Deutsch)", style_decl_title),
        ],
        [
            Paragraph(sanitize_text_for_pdf(aff_de, is_ttfont=has_ttfonts), style_decl_body),
        ]
    ]
    t_decl = Table(decl_data, colWidths=[505])
    t_decl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E0")),
        ('LINELEFT', (0, 0), (0, -1), 3.0, colors.HexColor("#111827")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t_decl)
    story.append(Spacer(1, 10))

    # 3. Academic Metadata Table (APA / Booktabs Monochrome Style)
    story.append(Paragraph("Academic Metadata / Akademische Metadaten", style_h3))
    models_used = doc.get_all_models_used()
    clean_name = sanitize_text_for_pdf(meta.student_name, is_ttfont=has_ttfonts)
    clean_matr = sanitize_text_for_pdf(meta.matriculation_number.strip() if meta.matriculation_number else "N/A", is_ttfont=has_ttfonts)
    meta_rows = [
        [Paragraph("Student Name / Name d. Studierenden", style_table_key), Paragraph(clean_name, style_table_val)],
        [Paragraph("Student ID / Matrikelnummer", style_table_key), Paragraph(clean_matr, style_table_val)],
    ]

    clean_degree = sanitize_text_for_pdf(meta.degree_program, is_ttfont=has_ttfonts)
    clean_course = sanitize_text_for_pdf(meta.course_code_title or "N/A", is_ttfont=has_ttfonts)
    clean_scope = sanitize_text_for_pdf(meta.assignment_scope or "N/A", is_ttfont=has_ttfonts)
    clean_exam = sanitize_text_for_pdf(meta.examiner or "N/A", is_ttfont=has_ttfonts)
    clean_models = sanitize_text_for_pdf(models_used, is_ttfont=has_ttfonts)

    meta_rows.extend([
        [Paragraph("Degree Program / Studiengang", style_table_key), Paragraph(clean_degree, style_table_val)],
        [Paragraph("Course Code &amp; Title / Lehrveranstaltung", style_table_key), Paragraph(clean_course, style_table_val)],
        [Paragraph("Assignment Scope / Umfang der Arbeit", style_table_key), Paragraph(clean_scope, style_table_val)],
        [Paragraph("Examiner / Supervisor / Betreuung", style_table_key), Paragraph(clean_exam, style_table_val)],
        [Paragraph("Submission Date / Abgabedatum", style_table_key), Paragraph(meta.submission_date, style_table_val)],
        [Paragraph("AI Models Utilized / Verwendete KI-Modelle", style_table_key), Paragraph(clean_models, style_table_val)],
    ])
    t_meta = Table(meta_rows, colWidths=[175, 330])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('LINEABOVE', (0, 0), (-1, 0), 1.2, colors.HexColor("#111827")),
        ('LINEBELOW', (0, 0), (-1, -2), 0.35, colors.HexColor("#E2E8F0")),
        ('LINEBELOW', (0, -1), (-1, -1), 1.2, colors.HexColor("#111827")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))

    # 4. Section A: Chronological Interaction Protocol
    sec_a_hdr = (
        "Section A: Chronological Interaction Protocol<br/>"
        "<font size='9' color='#4B5563'>Abschnitt A: Chronologisches Interaktionsprotokoll</font>"
    )
    story.append(Paragraph(sec_a_hdr, style_h3))

    if not doc.drops:
        story.append(Paragraph("<em>No interaction drops recorded / Keine Interaktions-Drops erfasst.</em>", style_body))
    else:
        for drop in doc.drops:
            decision = (
                drop.critical_examination.application_decision
                if drop.critical_examination
                else "Accepted"
            )
            scope = drop.context_scope.strip() if drop.context_scope else "General / Zero Context"

            # Header line: Drop #N, Intent, Engine, Timestamp - Monochrome
            hdr_text = (
                f"<b>Drop #{drop.drop_number}: {html.escape(drop.core_intent)}</b> — "
                f"<b>{html.escape(drop.target_engine)}</b> "
                f"<font color='#6B7280'>({html.escape(drop.timestamp)})</font>"
            )
            p_hdr = Paragraph(hdr_text, style_body)

            # Metadata line
            meta_line = (
                f"<b>Context Scope / Kontextbereich:</b> <i>{html.escape(scope)}</i> &nbsp;|&nbsp; "
                f"<b>Decision / Übernahmeentscheidung:</b> <b>[{html.escape(decision)}]</b>"
            )
            p_meta = Paragraph(meta_line, style_body)

            # Prompt block: Flowing Paragraph with fixed non-overlapping margin alignment
            p_prompt_label = Paragraph("RAW PROMPT / URSPRÜNGLICHER PROMPT", style_code_label)
            prompt_p = format_code_paragraph(drop.raw_prompt, style_code_prompt, is_ttfont=has_ttfonts)

            # Output block: Flowing Paragraph
            p_output_label = Paragraph("RAW AI OUTPUT / URSPRÜNGLICHE KI-ANTWORT", style_code_label)
            output_p = format_code_paragraph(drop.raw_output, style_code_output, is_ttfont=has_ttfonts)

            # Keep only the compact header together so it doesn't get orphaned at page bottom
            story.append(KeepTogether([p_hdr, p_meta, p_prompt_label]))
            story.append(prompt_p)

            # Output section
            story.append(p_output_label)
            story.append(output_p)

            # Generated Artifact / File Reference if present
            if drop.output_file_reference and drop.output_file_reference.strip():
                clean_ref = sanitize_text_for_pdf(drop.output_file_reference.strip(), is_ttfont=has_ttfonts)
                ref_text = (
                    "<b>📎 Generated Artifact Reference / Generierte Dateireferenz:</b> "
                    f"<u><b>{html.escape(clean_ref)}</b></u> "
                    "<font color='#4B5563'><i>(see accompanying submission files / siehe Einreichungsdateien)</i></font>"
                )
                story.append(Spacer(1, 3))
                story.append(Paragraph(ref_text, style_body))

            # Critical Reflection Box if present
            if drop.critical_examination and drop.critical_examination.flaws_plausibility.strip():
                clean_crit = sanitize_text_for_pdf(drop.critical_examination.flaws_plausibility.strip(), is_ttfont=has_ttfonts)
                crit_text = (
                    "<b>Critical Examination &amp; Plausibility Audit / Kritische Prüfung &amp; Plausibilitätsaudit:</b><br/>"
                    f"{html.escape(clean_crit)}"
                )
                p_crit = Paragraph(crit_text, style_critical)
                story.append(p_crit)

            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0"), spaceAfter=10))

    # 5. Section B: Fact-Checking Matrix Table (APA / Booktabs Monochrome Style)
    sec_b_hdr = (
        "Section B: Adversarial Fact-Checking Matrix<br/>"
        "<font size='9' color='#4B5563'>Abschnitt B: Matrix zur adversarialen Faktenprüfung</font>"
    )
    story.append(Paragraph(sec_b_hdr, style_h3))
    all_facts = doc.get_all_fact_checks()

    if not all_facts:
        story.append(Paragraph("<em>No adversarial fact-check claims recorded / Keine adversarialen Faktenprüfungen erfasst.</em>", style_body))
    else:
        th_style = ParagraphStyle("TH", parent=style_body, fontName=font_sans_bold, fontSize=8, leading=10.5, textColor=colors.HexColor("#111827"))
        td_style = ParagraphStyle("TD", parent=style_body, fontName=font_sans, fontSize=8, leading=10.5, textColor=colors.HexColor("#1F2937"))

        fc_rows = [[
            Paragraph("Ref / Nr.", th_style),
            Paragraph("Claim / Extrahierte Aussage", th_style),
            Paragraph("Primary Source / Primärquelle", th_style),
            Paragraph("Status", th_style),
            Paragraph("Audit Note / Prüfvermerk", th_style),
        ]]

        for fc in all_facts:
            ref = fc.drop_reference or "General"
            status_p = Paragraph(f"<b>[{html.escape(fc.status)}]</b>", td_style)
            clean_claim = sanitize_text_for_pdf(fc.claim, is_ttfont=has_ttfonts)
            clean_src = sanitize_text_for_pdf(fc.primary_source or "N/A", is_ttfont=has_ttfonts)
            clean_note = sanitize_text_for_pdf(fc.rectification_note or "None", is_ttfont=has_ttfonts)

            fc_rows.append([
                Paragraph(f"<b>{html.escape(ref)}</b>", td_style),
                Paragraph(html.escape(clean_claim), td_style),
                Paragraph(html.escape(clean_src), td_style),
                status_p,
                Paragraph(html.escape(clean_note), td_style),
            ])

        t_matrix = Table(fc_rows, colWidths=[55, 185, 125, 60, 80], repeatRows=1)
        t_style = [
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('LINEABOVE', (0, 0), (-1, 0), 1.2, colors.HexColor("#111827")),
            ('LINEBELOW', (0, 0), (-1, 0), 0.6, colors.HexColor("#111827")),
            ('LINEBELOW', (0, 1), (-1, -2), 0.35, colors.HexColor("#E2E8F0")),
            ('LINEBELOW', (0, -1), (-1, -1), 1.2, colors.HexColor("#111827")),
            ('TOPPADDING', (0, 0), (-1, -1), 4.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]
        t_matrix.setStyle(TableStyle(t_style))
        story.append(t_matrix)

    # 6. Section C: Verification & Audit Trail (Cryptographic Tamper-Evidence) - Monochrome
    story.append(Spacer(1, 14))
    sec_c_hdr = (
        "Section C: Verification &amp; Audit Trail<br/>"
        "<font size='9' color='#4B5563'>Abschnitt C: Verifikation &amp; Prüfpfad</font>"
    )
    story.append(Paragraph(sec_c_hdr, style_h3))

    hash_val = doc.compute_integrity_hash()
    timestamp_val = doc.hash_timestamp or get_current_cest_time()
    total_drops = len(doc.drops)
    total_facts = len(all_facts)

    audit_notice_text = (
        "<i>This cryptographic SHA-256 digest certifies the authenticity and integrity of this protocol at the time of export. "
        "Any subsequent manual alteration of recorded interactions invalidates this signature. / "
        "Diese kryptographische SHA-256-Prüfsumme bescheinigt die Authentizität und Unverfälschtheit dieses Protokolls "
        "zum Zeitpunkt des Exports. Jede nachträgliche manuelle Bearbeitung macht diese Signatur ungültig.</i>"
    )

    audit_rows = [
        [Paragraph("Document Integrity Hash / Prüfsumme", style_table_key), Paragraph(f"<font face='{font_mono}' size='7'><b>{hash_val}</b></font>", style_table_val)],
        [Paragraph("Audit Timestamp / Zeitstempel", style_table_key), Paragraph(timestamp_val, style_table_val)],
        [Paragraph("Total Drops Logged / Protokollierte Drops", style_table_key), Paragraph(str(total_drops), style_table_val)],
        [Paragraph("Audited Fact-Checks / Geprüfte Fakten", style_table_key), Paragraph(str(total_facts), style_table_val)],
        [Paragraph("Authenticity Notice / Hinweis", style_table_key), Paragraph(audit_notice_text, style_table_val)],
    ]
    t_audit = Table(audit_rows, colWidths=[175, 330])
    t_audit.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('LINEABOVE', (0, 0), (-1, 0), 1.2, colors.HexColor("#111827")),
        ('LINEBELOW', (0, 0), (-1, -2), 0.35, colors.HexColor("#E2E8F0")),
        ('LINEBELOW', (0, -1), (-1, -1), 1.2, colors.HexColor("#111827")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_audit)

    # Build PDF with dynamic 2-pass running headers and page numbers
    canvas_maker = NumberedCanvas.create_factory(
        student_name=meta.student_name,
        doc_title=doc.title,
        font_name=font_sans,
        student_id=meta.matriculation_number,
    )
    pdf_doc.build(story, canvasmaker=canvas_maker)
    return str(out_path)


# ==============================================================================
# Unified PDF Render Entry Point (100% Native ReportLab Engine)
# ==============================================================================

def find_browser_executable() -> Optional[str]:
    """Finds installed Microsoft Edge or Google Chrome executable on Windows."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def generate_html(doc: ProtocolDocument, css_content: Optional[str] = None) -> str:
    """Compiles ProtocolDocument into standalone, high-fidelity styled HTML."""
    if css_content is None:
        css_path = get_resource_path("styles.css")
        if css_path.exists():
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
        else:
            css_content = "body { font-family: Arial, sans-serif; }"

    doc.renumber_drops()
    meta = doc.metadata

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "<meta charset='utf-8'>",
        f"<title>{html.escape(doc.title)}</title>",
        f"<style>\n{css_content}\n</style>",
        "</head>",
        "<body>",
        "<h1>Generative AI Documentation &amp; Verification Protocol</h1>",
        "<h2>Anhang: Dokumentation und Verifikationsprotokoll</h2>",
        "<div class='declaration-box'>",
        "<div class='declaration-lang'>",
        "<div class='declaration-title'>Academic AI Use Declaration (English)</div>",
        f"{html.escape(meta.affidavit_en or AI_USE_STATEMENT_EN)}",
        "</div>",
        "<div class='declaration-lang'>",
        "<div class='declaration-title'>Erklärung zur Verwendung generativer KI (Deutsch)</div>",
        f"{html.escape(meta.affidavit_de or AI_USE_STATEMENT_DE)}",
        "</div>",
        "</div>",
        "<h3>Academic Metadata</h3>",
        "<table class='metadata-table'>",
        f"<tr><td>Student Name</td><td><strong>{html.escape(meta.student_name)}</strong></td></tr>",
        f"<tr><td>Degree Program</td><td>{html.escape(meta.degree_program)}</td></tr>",
        f"<tr><td>Course Code &amp; Title</td><td>{html.escape(meta.course_code_title or 'N/A')}</td></tr>",
        f"<tr><td>Assignment Scope</td><td>{html.escape(meta.assignment_scope or 'N/A')}</td></tr>",
        f"<tr><td>Examiner / Supervisor</td><td>{html.escape(meta.examiner or 'N/A')}</td></tr>",
        f"<tr><td>Submission Date</td><td>{html.escape(meta.submission_date)}</td></tr>",
        f"<tr><td>Primary AI Models</td><td>{html.escape(meta.primary_ai_models)}</td></tr>",
        f"<tr><td>Secondary AI Models</td><td>{html.escape(meta.secondary_ai_models)}</td></tr>",
        "</table>",
        "<h3>Section A: Chronological Interaction Protocol</h3>",
    ]

    for drop in doc.drops:
        decision = drop.critical_examination.application_decision if drop.critical_examination else "Accepted"
        scope = drop.context_scope.strip() if drop.context_scope else "General / Zero Context"
        html_parts.append(f"<div class='interaction-drop'>")
        html_parts.append(f"<h4>Drop #{drop.drop_number}: {html.escape(drop.core_intent)} — {html.escape(drop.target_engine)} ({html.escape(drop.timestamp)})</h4>")
        html_parts.append(f"<p><strong>Context Scope:</strong> {html.escape(scope)} | <strong>Decision:</strong> [{html.escape(decision)}]</p>")
        html_parts.append("<div class='code-label'>Raw Prompt</div>")
        html_parts.append(f"<pre>{html.escape(drop.raw_prompt)}</pre>")
        html_parts.append("<div class='code-label'>Raw Output</div>")
        html_parts.append(f"<pre>{html.escape(drop.raw_output)}</pre>")
        if drop.critical_examination and drop.critical_examination.flaws_plausibility.strip():
            html_parts.append(f"<div class='critical-box'><strong>Critical Plausibility Audit:</strong> {html.escape(drop.critical_examination.flaws_plausibility.strip())}</div>")
        html_parts.append("</div>")

    html_parts.append("<h3>Section B: Adversarial Fact-Checking Matrix</h3>")
    all_facts = doc.get_all_fact_checks()
    if all_facts:
        html_parts.append("<table><thead><tr><th>Ref</th><th>Claim</th><th>Primary Source</th><th>Status</th><th>Note</th></tr></thead><tbody>")
        for fc in all_facts:
            html_parts.append(f"<tr><td>{html.escape(fc.drop_reference or 'General')}</td><td>{html.escape(fc.claim)}</td><td>{html.escape(fc.primary_source or 'N/A')}</td><td>[{html.escape(fc.status)}]</td><td>{html.escape(fc.rectification_note or 'None')}</td></tr>")
        html_parts.append("</tbody></table>")

    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def render_to_pdf(doc: ProtocolDocument, output_pdf_path: str) -> str:
    """
    Renders ProtocolDocument to publication-ready vector PDF directly via ReportLab.
    100% self-contained in pure Python with zero external browser dependencies.
    """
    return render_to_pdf_reportlab(doc, output_pdf_path)


def open_in_system_viewer(file_path: str) -> None:
    """Launches file in the default system viewer (e.g. Acrobat or Edge for PDF)."""
    if sys.platform == "win32":
        os.startfile(file_path)
    else:
        import shutil
        opener = shutil.which("xdg-open") or shutil.which("open")
        if opener:
            subprocess.Popen([opener, file_path])
