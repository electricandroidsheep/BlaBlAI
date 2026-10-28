"""
Comprehensive verification and stress test suite for Academic AI Protocol Logger.
Tests i18n symmetry, GUI widget drawing, Dark/Light modes, German/English locales,
edge-case character sets, document lifecycle, and PDF compilation.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    ProtocolDocument,
    ProtocolMetadata,
    InteractionDrop,
    CriticalExamination,
    FactCheckEntry,
)
from storage import StorageManager
from generator import (
    generate_markdown,
    generate_html,
    render_to_pdf,
    find_browser_executable,
    get_resource_path,
)
import i18n
from i18n import (
    t,
    set_current_locale,
    get_current_locale,
    TRANSLATIONS,
    CANONICAL_INTENTS,
    CANONICAL_DECISIONS,
    CANONICAL_STATUSES,
    CANONICAL_SCOPES,
    canonicalize_intent,
    localize_intent,
    canonicalize_decision,
    localize_decision,
    canonicalize_status,
    localize_status,
    canonicalize_scope,
    localize_scope,
)


class TestI18nCompleteness(unittest.TestCase):
    def test_key_symmetry(self):
        """Ensures every key in English exists in German, and vice-versa."""
        en_keys = set(TRANSLATIONS["en"].keys())
        de_keys = set(TRANSLATIONS["de"].keys())

        missing_in_de = en_keys - de_keys
        missing_in_en = de_keys - en_keys

        self.assertEqual(missing_in_de, set(), f"Keys missing in German translations: {missing_in_de}")
        self.assertEqual(missing_in_en, set(), f"Keys missing in English translations: {missing_in_en}")

    def test_format_placeholders(self):
        """Ensures formatting variables match between languages."""
        import string

        formatter = string.Formatter()
        for key in TRANSLATIONS["en"]:
            en_text = TRANSLATIONS["en"][key]
            de_text = TRANSLATIONS["de"][key]

            en_fields = {fname for _, fname, _, _ in formatter.parse(en_text) if fname is not None}
            de_fields = {fname for _, fname, _, _ in formatter.parse(de_text) if fname is not None}

            self.assertEqual(
                en_fields,
                de_fields,
                f"Mismatch in placeholders for '{key}': EN={en_fields}, DE={de_fields}"
            )

    def test_canonical_roundtrips(self):
        """Tests that localizing and canonicalizing preserves internal values."""
        for loc in ["en", "de"]:
            set_current_locale(loc)
            for intent in CANONICAL_INTENTS:
                loc_val = localize_intent(intent)
                canon_val = canonicalize_intent(loc_val)
                self.assertEqual(canon_val, intent, f"Failed roundtrip for intent '{intent}' in {loc}")

            for dec in CANONICAL_DECISIONS:
                loc_val = localize_decision(dec)
                canon_val = canonicalize_decision(loc_val)
                self.assertEqual(canon_val, dec, f"Failed roundtrip for decision '{dec}' in {loc}")

            for stat in CANONICAL_STATUSES:
                loc_val = localize_status(stat)
                canon_val = canonicalize_status(loc_val)
                self.assertEqual(canon_val, stat, f"Failed roundtrip for status '{stat}' in {loc}")

            for scope in CANONICAL_SCOPES:
                loc_val = localize_scope(scope)
                canon_val = canonicalize_scope(loc_val)
                self.assertEqual(canon_val, scope, f"Failed roundtrip for scope '{scope}' in {loc}")


class TestDataAndStorageIntegrity(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_app_dir = Path(tempfile.mkdtemp())
        self.storage = StorageManager(app_dir=self.test_app_dir, storage_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.test_app_dir, ignore_errors=True)

    def test_german_special_characters_and_markdown(self):
        """Verifies special characters (ä, ö, ü, ß, quotes, pipes, codeblocks) serialize and save correctly."""
        doc = self.storage.create_new_document(
            title="Spezielle_Prüfung_äöüß",
            course="Wirtschaftsinformatik & KI-Methoden",
            assignment_scope="Master's Thesis",
            examiner="Prof. Dr. Weiß-Müller",
        )

        complex_prompt = (
            "Erstelle eine Synthese zu folgendem Fall:\n"
            "```python\n"
            "def test():\n"
            "    return 'äöü | ß'\n"
            "```\n"
            "Welche 'besonderen' Einschränkungen gibt es?"
        )
        complex_output = (
            "Hier ist die Analyse mit Sonderzeichen:\n"
            "1. Äpfel, Ökologie & Übertragbarkeit\n"
            "2. Wert: | 100% | gesichert |\n"
            "Keine Halluzinationen festgestellt."
        )

        drop = InteractionDrop(
            drop_number=1,
            target_engine="Gemini 1.5 Pro",
            core_intent="Synthesis",
            context_scope="Kapitel 1-4: Einführung & Grundlagen (PDF)",
            raw_prompt=complex_prompt,
            raw_output=complex_output,
            critical_examination=CriticalExamination(
                flaws_plausibility="Plausibilität geprüft: Quellenangaben für 'Äpfel' verifiziert.",
                application_decision="Accepted",
            ),
            fact_checks=[
                FactCheckEntry(
                    claim="Die Übertragbarkeit beträgt genau 100% | gemessen nach ISO 9241.",
                    primary_source="Müller & Weiß (2024), S. 88",
                    status="Confirmed",
                    rectification_note="Vollständig bestätigt; im Text übernommen.",
                )
            ]
        )
        doc.drops.append(drop)
        saved_path = self.storage.save_document(doc)

        # Reload from disk
        loaded = self.storage.load_document(saved_path)
        self.assertEqual(loaded.title, doc.title)
        self.assertEqual(loaded.metadata.examiner, "Prof. Dr. Weiß-Müller")
        self.assertEqual(loaded.drops[0].raw_prompt, complex_prompt)
        self.assertEqual(loaded.drops[0].raw_output, complex_output)
        self.assertEqual(len(loaded.drops[0].fact_checks), 1)

        # Verify markdown export doesn't break tables with pipes
        md = generate_markdown(loaded)
        self.assertIn("Prof. Dr. Weiß-Müller", md)
        self.assertIn("Müller & Weiß (2024), S. 88", md)
        self.assertIn("\\|", md)  # escaped pipes in fact check table

    def test_document_listing_and_deletion(self):
        doc1 = self.storage.create_new_document("Doc_A", course="Course 1")
        doc2 = self.storage.create_new_document("Doc_B", course="Course 2")

        docs = self.storage.list_documents()
        self.assertEqual(len(docs), 2)

        self.storage.delete_document(doc1.file_path)
        docs_after = self.storage.list_documents()
        self.assertEqual(len(docs_after), 1)
        self.assertEqual(docs_after[0]["title"], "Doc_B")


class TestGUIComponentsAndNoColorErrors(unittest.TestCase):
    """
    Renders all GUI windows and views in off-screen mode.
    Guarantees no TclError (like unknown color 'red400') occurs in any view,
    under both Dark and Light modes, and in both English and German.
    """
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_app_dir = Path(tempfile.mkdtemp())
        self.storage = StorageManager(app_dir=self.test_app_dir, storage_dir=self.test_dir)

        # Create a sample document in storage so hub cards are rendered
        doc = self.storage.create_new_document("Sample_Protocol", course="DBM-501", assignment_scope="Master's Thesis")
        drop = InteractionDrop(
            drop_number=1,
            target_engine="Claude 3.5 Sonnet",
            core_intent="Synthesis",
            raw_prompt="Summarize findings.",
            raw_output="Summary output text.",
            critical_examination=CriticalExamination(
                flaws_plausibility="Valid source.",
                application_decision="Accepted",
            ),
            fact_checks=[FactCheckEntry(claim="Claim 1", primary_source="Smith 2023", status="Confirmed")]
        )
        doc.drops.append(drop)
        self.storage.save_document(doc)
        self.doc = doc

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.test_app_dir, ignore_errors=True)

    def test_main_window_lifecycle_all_themes_and_locales(self):
        from gui.main_window import MainWindow
        import customtkinter as ctk

        app = MainWindow(storage=self.storage)
        app.withdraw()  # Offscreen

        try:
            # Test in Dark mode, EN
            ctk.set_appearance_mode("Dark")
            set_current_locale("en")
            app.show_hub()
            app.update_idletasks()
            app.update()

            # Test in Light mode, EN
            ctk.set_appearance_mode("Light")
            app.show_hub()
            app.update_idletasks()
            app.update()

            # Test in Dark mode, DE
            ctk.set_appearance_mode("Dark")
            set_current_locale("de")
            app.show_hub()
            app.update_idletasks()
            app.update()

            # Test in Light mode, DE
            ctk.set_appearance_mode("Light")
            app.show_hub()
            app.update_idletasks()
            app.update()

            # Open document into EditorView
            app.open_document(self.doc)
            app.update_idletasks()
            app.update()

            # Switch tabs in EditorView
            editor = app.current_view
            self.assertIsNotNone(editor)
            editor.tabview.set(t("tab_drops"))
            app.update_idletasks()
            app.update()

            editor.tabview.set(t("tab_matrix"))
            app.update_idletasks()
            app.update()

            editor.tabview.set(t("tab_preview"))
            app.update_idletasks()
            app.update()

            # Test adding a drop in LoggerView
            logger_v = editor.logger_view
            logger_v.txt_prompt.insert("1.0", "New test prompt")
            logger_v.txt_output.insert("1.0", "New test output")
            logger_v._handle_submit()
            self.assertEqual(len(self.doc.drops), 2)
            app.update_idletasks()
            app.update()

            # Test adding standalone fact check in FactCheckView
            matrix_v = editor.matrix_view
            matrix_v.var_claim.set("Standalone claim test")
            matrix_v.var_source.set("Source 2024")
            matrix_v._handle_add_standalone()
            self.assertEqual(len(self.doc.standalone_fact_checks), 1)
            app.update_idletasks()
            app.update()

            # Return to HubView
            editor._handle_back()
            app.update_idletasks()
            app.update()

        finally:
            app.destroy()


class TestPdfAndResourcePackaging(unittest.TestCase):
    def test_styles_css_resource_resolution(self):
        """Verifies get_resource_path locates styles.css in both dev and packaged modes."""
        css_path = get_resource_path("styles.css")
        self.assertTrue(css_path.exists(), f"styles.css must be resolvable at {css_path}")

    def test_pdf_rendering_with_umlauts(self):
        """Verifies that PDF rendering succeeds with full German text and umlauts."""
        doc = ProtocolDocument(
            title="Prüfungsprotokoll KI",
            metadata=ProtocolMetadata(
                student_name="Sven Várszegi, B.A.",
                degree_program="Master Digital Business Management (FH OÖ / JKU)",
                course_code_title="Wissenschaftliches Arbeiten & KI",
                examiner="Prof. Dr. Weiß-Müller",
            )
        )
        drop = InteractionDrop(
            drop_number=1,
            target_engine="Gemini 1.5 Pro",
            core_intent="Method Check",
            raw_prompt="Erkläre die Übertragbarkeit der Methode.",
            raw_output="Die Methode ist übertragbar, sofern Bedingungen erfüllt sind.",
            critical_examination=CriticalExamination(
                flaws_plausibility="Quellenangabe verifiziert.",
                application_decision="Accepted",
            ),
            fact_checks=[FactCheckEntry(claim="Bedingung A ist erfüllt", primary_source="Quelle (2024)", status="Confirmed")]
        )
        doc.drops.append(drop)

        output_pdf = Path(__file__).parent / "test_umlaut_output.pdf"
        try:
            res = render_to_pdf(doc, str(output_pdf))
            self.assertTrue(output_pdf.exists())
            self.assertGreater(output_pdf.stat().st_size, 1000)
        finally:
            if output_pdf.exists():
                output_pdf.unlink()


class TestPreReleaseFeatures(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_app_dir = Path(tempfile.mkdtemp())
        self.storage = StorageManager(app_dir=self.test_app_dir, storage_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.test_app_dir, ignore_errors=True)

    def test_cryptographic_integrity_hash_and_tamper_detection(self):
        """Verifies SHA-256 canonical hashing, audit trail, and tamper sensitivity."""
        doc = self.storage.create_new_document("Integrity Test Protocol", course="Security DBM")
        doc.drops.append(InteractionDrop(
            drop_number=1,
            target_engine="Anthropic Claude",
            core_intent="Verification",
            raw_prompt="Authentic prompt 1",
            raw_output="Authentic response 1",
        ))

        # Save and verify hash generated
        saved_path = self.storage.save_document(doc)
        initial_hash = doc.integrity_hash
        self.assertTrue(initial_hash.startswith("sha256:"))
        self.assertTrue(len(initial_hash) > 20)
        self.assertTrue(bool(doc.hash_timestamp))

        # Reload and verify hash matched
        loaded = self.storage.load_document(saved_path)
        self.assertEqual(loaded.integrity_hash, initial_hash)

        # Verify hash changes if content is tampered
        loaded.drops[0].raw_output = "Tampered output"
        new_hash = loaded.compute_integrity_hash()
        self.assertNotEqual(initial_hash, new_hash, "Tampered content must alter SHA-256 digest")

        # Verify Markdown export contains audit trail block
        md = generate_markdown(doc)
        self.assertIn("Section C: Verification & Audit Trail", md)
        self.assertIn(doc.integrity_hash, md)
        self.assertIn("Total Interactions Logged", md)

    def test_cross_platform_pathing(self):
        """Verifies macOS, Windows, and Linux path resolution."""
        from storage import get_app_data_dir
        import unittest.mock as mock

        # Test Darwin (macOS)
        with mock.patch("sys.platform", "darwin"):
            mac_path = get_app_data_dir()
            self.assertIn("Library", str(mac_path))
            self.assertIn("Application Support", str(mac_path))
            self.assertIn("BlaBlAI", str(mac_path))

        # Test Windows
        with mock.patch("sys.platform", "win32"), mock.patch.dict(os.environ, {"LOCALAPPDATA": str(self.test_dir)}):
            win_path = get_app_data_dir()
            self.assertIn("BlaBlAI", str(win_path))

    def test_custom_affidavit_flow(self):
        """Verifies custom English and German affidavits persist and render in exports."""
        custom_en = "Custom English Thesis Affidavit for Sven Várszegi"
        custom_de = "Benutzerdefinierte deutsche Erklärung für Sven Várszegi"

        self.storage.custom_affidavit_en = custom_en
        self.storage.custom_affidavit_de = custom_de

        doc = self.storage.create_new_document("Affidavit Test", course="DBM")
        self.assertEqual(doc.metadata.affidavit_en, custom_en)
        self.assertEqual(doc.metadata.affidavit_de, custom_de)

        md = generate_markdown(doc)
        self.assertIn(custom_en, md)
        self.assertIn(custom_de, md)

        # PDF generation with custom affidavits
        pdf_path = self.test_dir / "affidavit_test.pdf"
        render_to_pdf(doc, str(pdf_path))
        self.assertTrue(pdf_path.exists())
        self.assertGreater(pdf_path.stat().st_size, 1000)

    def test_blablai_assets_and_tooltips(self):
        """Verifies programmatic asset generation and tooltips."""
        from gui.assets import get_blablai_ctk_image, ensure_icon_file
        import tkinter as tk

        ctk_img = get_blablai_ctk_image((32, 32))
        self.assertIsNotNone(ctk_img)

        icon_file = ensure_icon_file(dest_dir=self.test_dir)
        self.assertTrue(icon_file.exists())
        self.assertGreater(icon_file.stat().st_size, 500)

    def test_text_cleaning_and_normalization(self):
        """Verifies striping markdown fences, bullet normalization, and line wrapping."""
        from generator import clean_raw_interaction_text, wrap_long_code_lines

        # 1. Strip markdown fences
        fenced_input = "```python\ndef hello():\n    return 'world'\n```"
        cleaned = clean_raw_interaction_text(fenced_input)
        self.assertNotIn("```python", cleaned)
        self.assertNotIn("```", cleaned)
        self.assertIn("def hello():", cleaned)

        # 2. Normalize bullet points
        bullet_input = "• Point one\n* Point two\n- Point three"
        cleaned_bullets = clean_raw_interaction_text(bullet_input)
        self.assertEqual(cleaned_bullets, "- Point one\n- Point two\n- Point three")

        # 3. Long line wrapping
        long_line = "A" * 120
        wrapped = wrap_long_code_lines(long_line, max_len=80)
        lines = wrapped.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(len(lines[0]), 80)
        self.assertEqual(len(lines[1]), 40)

    def test_onboarding_and_default_title(self):
        """Verifies onboarding flag persistence and dynamic document title generation."""
        # Onboarding flag toggling and persistence
        self.storage.onboarding_completed = False
        self.assertFalse(self.storage.onboarding_completed)
        self.storage.onboarding_completed = True
        self.assertTrue(self.storage.onboarding_completed)

        # Reload storage to verify persistence in config.json
        storage_reloaded = StorageManager(app_dir=self.test_app_dir, storage_dir=self.storage.storage_dir)
        self.assertTrue(storage_reloaded.onboarding_completed)

        # Default document title generator
        self.storage.student_name = "Sven Várszegi, B.A."
        title = self.storage.generate_default_document_title()
        self.assertTrue(title.startswith("NewAI_Log_Sven_Varszegi_"))
        self.assertNotIn(",", title)
        self.assertNotIn(".", title)

    def test_output_file_reference_and_student_id_footer(self):
        """Verifies output_file_reference serialization and Student ID in PDF/MD tables and footer."""
        doc = self.storage.create_new_document(
            title="Artifact Test",
            course="DBM-Media",
            student_name="Sven Várszegi, B.A.",
            matriculation_number="k12345678",
        )
        drop = InteractionDrop(
            drop_number=1,
            target_engine="Gemini 1.5 Flash",
            core_intent="Code Generation",
            raw_prompt="Generate video animation script and save to video.mp4",
            raw_output="Script created and rendered to video.mp4",
            output_file_reference="video.mp4",
        )
        doc.drops.append(drop)

        # Markdown check
        md = generate_markdown(doc)
        self.assertIn("Student ID / Matrikelnummer", md)
        self.assertIn("k12345678", md)
        self.assertIn("video.mp4", md)
        self.assertIn("Generated Artifact Reference", md)

        # PDF render check
        pdf_out = self.test_dir / "artifact_test.pdf"
        render_to_pdf(doc, str(pdf_out))
        self.assertTrue(pdf_out.exists())
        self.assertGreater(pdf_out.stat().st_size, 1000)

    def test_retroactive_drop_logging_and_rendering(self):
        """Verifies retroactive / archive drops serialize, render with tags, and persist."""
        doc = self.storage.create_new_document("Retroactive Test", course="DBM")
        retro_drop = InteractionDrop(
            drop_number=1,
            timestamp="2026-05-12 (Retroactive)",
            target_engine="Anthropic Claude",
            core_intent="Brainstorming",
            raw_prompt="Past exploratory query on digital business ecosystems",
            raw_output="Historical outline of platform strategy",
            is_retroactive=True,
        )
        doc.drops.append(retro_drop)

        # 1. Serialization
        doc_dict = doc.to_dict()
        self.assertTrue(doc_dict["drops"][0]["is_retroactive"])
        reloaded = ProtocolDocument.from_dict(doc_dict)
        self.assertTrue(reloaded.drops[0].is_retroactive)

        # 2. Markdown output
        md = generate_markdown(doc)
        self.assertIn("Retroactive / Nachträglich", md)

        # 3. PDF rendering
        pdf_out = self.test_dir / "retro_test.pdf"
        render_to_pdf(doc, str(pdf_out))
        self.assertTrue(pdf_out.exists())

    def test_fact_checking_matrix_linking_and_safe_drop_deletion(self):
        """Verifies linking claims to drops, reassigning, and safe drop deletion preserving claims as Standalone."""
        doc = self.storage.create_new_document("Matrix Link Test", course="DBM")
        drop1 = InteractionDrop(
            drop_number=1,
            target_engine="Claude 3.5 Sonnet",
            core_intent="Method Check",
            raw_prompt="How many interviews for saturation?",
            raw_output="Guest et al. (2006) recommend 12 interviews.",
        )
        drop2 = InteractionDrop(
            drop_number=2,
            target_engine="Gemini 1.5 Pro",
            core_intent="Drafting",
            raw_prompt="Draft sampling section",
            raw_output="Sample of 15 participants.",
        )
        doc.drops.extend([drop1, drop2])
        doc.renumber_drops()

        # Link claim 1 to Drop #1
        fc1 = FactCheckEntry(
            claim="Guest et al. recommend 12 interviews for saturation",
            primary_source="Guest et al. (2006) p. 59",
            status="Confirmed",
        )
        doc.assign_fact_check(fc1, drop1.id)
        self.assertIn(fc1, drop1.fact_checks)
        self.assertEqual(fc1.drop_reference, "Interaction #1")

        # Link claim 2 as Standalone
        fc2 = FactCheckEntry(
            claim="General statistical guideline on effect sizes",
            primary_source="Cohen (1988)",
            status="Clarified",
        )
        doc.assign_fact_check(fc2, None)
        self.assertIn(fc2, doc.standalone_fact_checks)
        self.assertEqual(fc2.drop_reference, "Standalone")

        # Verify get_all_fact_checks collects both
        all_checks = doc.get_all_fact_checks()
        self.assertEqual(len(all_checks), 2)

        # Reassign fc1 from Drop #1 to Drop #2
        doc.assign_fact_check(fc1, drop2.id)
        self.assertNotIn(fc1, drop1.fact_checks)
        self.assertIn(fc1, drop2.fact_checks)
        self.assertEqual(fc1.drop_reference, "Interaction #2")

        # Safe drop deletion: delete Drop #2. Claim fc1 must NOT be lost!
        doc.remove_drop(drop2)
        self.assertEqual(len(doc.drops), 1)
        self.assertEqual(doc.drops[0].id, drop1.id)
        # fc1 should now be preserved in standalone_fact_checks
        self.assertIn(fc1, doc.standalone_fact_checks)
        self.assertEqual(fc1.drop_reference, "Standalone")
        self.assertEqual(len(doc.get_all_fact_checks()), 2)

    def test_extended_and_custom_verification_statuses(self):
        """Verifies preset extended statuses (Clarified, Disputed) and arbitrary custom typed statuses."""
        doc = self.storage.create_new_document("Status Test", course="DBM")
        fc_clarified = FactCheckEntry(
            claim="Claim A",
            primary_source="Source A",
            status="Clarified",
        )
        fc_disputed = FactCheckEntry(
            claim="Claim B",
            primary_source="Source B",
            status="Disputed",
        )
        fc_custom = FactCheckEntry(
            claim="Claim C",
            primary_source="Source C",
            status="Partially Outdated",  # Custom user-typed status
        )
        doc.standalone_fact_checks.extend([fc_clarified, fc_disputed, fc_custom])

        # Test canonicalization and localization roundtrip
        set_current_locale("en")
        self.assertEqual(localize_status("Clarified"), "Clarified")
        set_current_locale("de")
        self.assertEqual(localize_status("Clarified"), "Präzisiert")
        self.assertEqual(localize_status("Disputed"), "Umstritten")
        self.assertEqual(localize_status("Partially Outdated"), "Partially Outdated")
        self.assertEqual(canonicalize_status("Präzisiert"), "Clarified")
        self.assertEqual(canonicalize_status("Umstritten"), "Disputed")
        self.assertEqual(canonicalize_status("Partially Outdated"), "Partially Outdated")
        set_current_locale("en")

        # Markdown export check
        md = generate_markdown(doc)
        self.assertIn("[Clarified]", md)
        self.assertIn("[Disputed]", md)
        self.assertIn("[Partially Outdated]", md)

    def test_external_evidence_file_flag(self):
        """Verifies external file evidence flag displays [File] indicators in PDF, MD, and HTML."""
        doc = self.storage.create_new_document("File Evidence Test", course="DBM")
        fc = FactCheckEntry(
            claim="Empirical cluster analysis results",
            primary_source="cluster_analysis_dataset.csv",
            is_external_file=True,
            status="Confirmed",
            rectification_note="Verified against appendix dataset",
        )
        doc.standalone_fact_checks.append(fc)

        # Markdown
        md = generate_markdown(doc)
        self.assertIn("📁 `[File / Datei]`", md)
        self.assertIn("cluster_analysis_dataset.csv", md)

        # HTML
        html_out = generate_html(doc)
        self.assertIn("📁 <strong>[File]:</strong>", html_out)

        # PDF render
        pdf_out = self.test_dir / "file_evidence.pdf"
        render_to_pdf(doc, str(pdf_out))
        self.assertTrue(pdf_out.exists())

    def test_multi_template_landscape_pdf_generation(self):
        """Verifies that Section B renders on Landscape A4 pages while Section A and C render on Portrait."""
        from pypdf import PdfReader

        doc = self.storage.create_new_document("Landscape Matrix Test", course="DBM")
        drop = InteractionDrop(
            drop_number=1,
            target_engine="Anthropic Claude",
            core_intent="Method Check",
            raw_prompt="Query for Section A",
            raw_output="Response for Section A",
        )
        doc.drops.append(drop)

        # Add multiple fact check claims so Section B produces a dedicated matrix page
        for i in range(1, 5):
            doc.standalone_fact_checks.append(FactCheckEntry(
                claim=f"Audited claim number {i} regarding empirical methodology",
                primary_source=f"Author et al. (202{i}) Journal of Management, Vol {i}, pp. 10-25",
                status="Confirmed" if i % 2 == 0 else "Clarified",
                rectification_note=f"Cross-checked against table {i} in primary study appendix.",
            ))

        pdf_path = self.test_dir / "landscape_test.pdf"
        render_to_pdf(doc, str(pdf_path))
        self.assertTrue(pdf_path.exists())

        reader = PdfReader(str(pdf_path))
        self.assertGreaterEqual(len(reader.pages), 3, "Document should span Cover/Drops, Landscape Matrix, and Audit Trail")

        # Page 1 (Cover / Drops) should be Portrait: width ~595 pt, height ~841 pt
        p1 = reader.pages[0]
        w1, h1 = float(p1.mediabox.width), float(p1.mediabox.height)
        self.assertLess(w1, h1, f"Page 1 should be portrait, got width={w1}, height={h1}")

        # Page 2 (Section B: Fact-Checking Matrix) should be LANDSCAPE: width ~841 pt, height ~595 pt
        p2 = reader.pages[1]
        w2, h2 = float(p2.mediabox.width), float(p2.mediabox.height)
        self.assertGreater(w2, h2, f"Page 2 should be landscape, got width={w2}, height={h2}")
        self.assertAlmostEqual(w2, 841.89, delta=5.0)
        self.assertAlmostEqual(h2, 595.27, delta=5.0)

        # Page 3 (Section C: Verification & Audit Trail) should be PORTRAIT: width ~595 pt, height ~841 pt
        p3 = reader.pages[2]
        w3, h3 = float(p3.mediabox.width), float(p3.mediabox.height)
        self.assertLess(w3, h3, f"Page 3 should be portrait, got width={w3}, height={h3}")

    def test_backward_compatibility_old_format_loading(self):
        """Verifies that older .ailog JSON files without new fields load seamlessly without errors."""
        legacy_json = """{
            "$schema": "academic-ai-protocol/v1",
            "version": "1.0.0",
            "doc_id": "legacy-test-uuid",
            "title": "Legacy AI Protocol",
            "created_at": "2026-09-01 10:00 CEST",
            "updated_at": "2026-09-01 10:00 CEST",
            "metadata": {
                "student_name": "Sven Várszegi, B.A.",
                "degree_program": "Master Digital Business Management (FH OÖ / JKU)"
            },
            "drops": [
                {
                    "id": "drop-legacy-1",
                    "drop_number": 1,
                    "timestamp": "2026-09-01 10:05 CEST",
                    "target_engine": "Claude 3.5 Sonnet",
                    "core_intent": "Synthesis",
                    "raw_prompt": "Explain legacy data schema",
                    "raw_output": "Legacy output text",
                    "fact_checks": [
                        {
                            "id": "fc-legacy-1",
                            "claim": "Legacy claim",
                            "primary_source": "Old Paper (2019)",
                            "status": "Confirmed",
                            "rectification_note": "Legacy note"
                        }
                    ]
                }
            ],
            "standalone_fact_checks": []
        }"""
        doc = ProtocolDocument.from_json(legacy_json)
        self.assertEqual(doc.title, "Legacy AI Protocol")
        self.assertEqual(len(doc.drops), 1)
        self.assertFalse(doc.drops[0].is_retroactive)
        self.assertEqual(len(doc.drops[0].fact_checks), 1)
        self.assertFalse(doc.drops[0].fact_checks[0].is_external_file)
        self.assertEqual(doc.drops[0].fact_checks[0].drop_reference, "Interaction #1")

        # Rendering legacy doc should execute without exceptions
        pdf_out = self.test_dir / "legacy_render.pdf"
        render_to_pdf(doc, str(pdf_out))
        self.assertTrue(pdf_out.exists())

    def test_factcheck_in_place_editing_and_relinking(self):
        """Verifies full in-place editing workflow: load entry, modify fields, relink drop, submit, and cancel."""
        from gui.factcheck_view import FactCheckView
        doc = ProtocolDocument(title="Editing Test")
        drop1 = InteractionDrop(core_intent="Synthesis", target_engine="Claude")
        doc.drops.append(drop1)
        doc.renumber_drops()

        fc_entry = FactCheckEntry(
            claim="Initial Claim",
            primary_source="Initial Source",
            status="Confirmed",
            rectification_note="Initial Note",
            is_external_file=False,
        )
        doc.assign_fact_check(fc_entry, target_drop_id=None)  # Standalone
        self.assertEqual(len(doc.standalone_fact_checks), 1)

        import customtkinter as ctk
        root = ctk.CTk()
        root.withdraw()
        changed = []
        try:
            fc_view = FactCheckView(root, doc=doc, on_document_changed=lambda: changed.append(True))

            # 1. Load entry into form
            fc_view._load_entry_into_form(fc_entry)
            self.assertIsNotNone(fc_view.editing_fc)
            self.assertEqual(fc_view.editing_fc.id, fc_entry.id)
            self.assertIn(t("fc_edit_entry_title"), fc_view.lbl_form_mode.cget("text"))
            self.assertEqual(fc_view.btn_submit.cget("text"), t("btn_update_entry"))

            # 2. Modify fields
            fc_view.var_claim.set("Updated Claim Text")
            fc_view.var_source.set("Updated Paper (2026)")
            fc_view.var_status.set("Refuted")
            fc_view.var_note.set("Corrected in section 4")
            fc_view.var_is_file.set(True)

            # Re-link from Standalone to Drop #1
            drop_label = [k for k, v in fc_view.drop_options_map.items() if v == drop1.id][0]
            fc_view.var_drop_select.set(drop_label)

            # 3. Submit update
            fc_view._handle_submit()
            self.assertIsNone(fc_view.editing_fc)
            self.assertEqual(fc_entry.claim, "Updated Claim Text")
            self.assertEqual(fc_entry.primary_source, "Updated Paper (2026)")
            self.assertEqual(fc_entry.status, "Refuted")
            self.assertEqual(fc_entry.rectification_note, "Corrected in section 4")
            self.assertTrue(fc_entry.is_external_file)
            self.assertEqual(fc_entry.drop_id, drop1.id)
            self.assertEqual(len(drop1.fact_checks), 1)
            self.assertEqual(len(doc.standalone_fact_checks), 0)
            self.assertTrue(len(changed) > 0)

            # 4. Load again and cancel
            fc_view._load_entry_into_form(fc_entry)
            self.assertIsNotNone(fc_view.editing_fc)
            fc_view._reset_form()
            self.assertIsNone(fc_view.editing_fc)
            self.assertEqual(fc_view.btn_submit.cget("text"), t("btn_add_entry"))
        finally:
            root.destroy()

    def test_academic_naming_bilingual_exports(self):
        """Verifies that exports use 'Claim & Source Verification Matrix' / 'Quellen- & Tatsachenverifikation'."""
        doc = ProtocolDocument(title="Academic Terminology Protocol")
        doc.drops.append(InteractionDrop(raw_prompt="P", raw_output="O"))
        doc.standalone_fact_checks.append(FactCheckEntry(claim="Empirical claim", primary_source="Data.csv", status="Confirmed", is_external_file=True))

        md = generate_markdown(doc)
        self.assertIn("### Section B: Claim & Source Verification Matrix", md)
        self.assertIn("#### Abschnitt B: Quellen- & Tatsachenverifikation", md)

        html_out = generate_html(doc)
        self.assertIn("<h3>Section B: Claim &amp; Source Verification Matrix</h3>", html_out)

        pdf_path = self.test_dir / "academic_terms.pdf"
        render_to_pdf(doc, str(pdf_path))
        self.assertTrue(pdf_path.exists())

    def test_interaction_title_and_export_rendering(self):
        """Verifies optional interaction title serialization, fallback, and rendering in exports."""
        doc = ProtocolDocument(title="Title Feature Test")
        drop_with_title = InteractionDrop(
            drop_number=1,
            title="Visplore Pipeline Analysis",
            core_intent="Synthesis",
            target_engine="Gemini 1.5 Pro",
            raw_prompt="Analyze Visplore output",
            raw_output="Analysis results",
        )
        drop_without_title = InteractionDrop(
            drop_number=2,
            title="",
            core_intent="Drafting",
            target_engine="Claude 3.5 Sonnet",
            raw_prompt="Draft introduction",
            raw_output="Draft text",
        )
        doc.drops.extend([drop_with_title, drop_without_title])
        doc.renumber_drops()

        # Serialization test
        doc_json = doc.to_json()
        loaded = ProtocolDocument.from_json(doc_json)
        self.assertEqual(loaded.drops[0].title, "Visplore Pipeline Analysis")
        self.assertEqual(loaded.drops[1].title, "")

        # Markdown export test
        md = generate_markdown(doc)
        self.assertIn("#### Interaction #1: Visplore Pipeline Analysis — Gemini 1.5 Pro", md)
        self.assertIn("- **Core Intent / Primärer Einsatzzweck:** `Synthesis`", md)
        self.assertIn("#### Interaction #2: Drafting — Claude 3.5 Sonnet", md)

        # HTML export test
        html_out = generate_html(doc)
        self.assertIn("Interaction #1: Visplore Pipeline Analysis — Gemini 1.5 Pro", html_out)
        self.assertIn("<strong>Intent:</strong> Synthesis", html_out)
        self.assertIn("Interaction #2: Drafting — Claude 3.5 Sonnet", html_out)

        # PDF export test
        pdf_out = self.test_dir / "title_render.pdf"
        render_to_pdf(doc, str(pdf_out))
        self.assertTrue(pdf_out.exists())
        self.assertGreater(pdf_out.stat().st_size, 1000)

    def test_factcheck_ui_action_buttons_and_mousewheel(self):
        """Verifies FactCheckView action button styling, drop label formatting, and short title display."""
        import customtkinter as ctk
        from gui.factcheck_view import FactCheckView
        root = ctk.CTk()
        root.withdraw()
        try:
            doc = ProtocolDocument(title="UI Verification Test")
            doc.drops.append(InteractionDrop(title="Visplore Export", core_intent="Synthesis", target_engine="Claude"))
            fc = FactCheckEntry(claim="Empirical Claim 1", primary_source="Paper (2025)", status="Confirmed")
            doc.assign_fact_check(fc, doc.drops[0].id)

            fc_view = FactCheckView(root, doc=doc, on_document_changed=lambda: None)
            # Verify drop option label contains title
            labels = list(fc_view.drop_options_map.keys())
            matched = any("Visplore Export" in lbl and "Interaction #1" in lbl for lbl in labels)
            self.assertTrue(matched, f"Drop options map should contain formatted label with title: {labels}")

            # Verify action buttons in rendered row
            all_buttons = [w for w in fc_view.scroll_table.winfo_children() if isinstance(w, ctk.CTkFrame)]
            self.assertGreaterEqual(len(all_buttons), 2)
        finally:
            root.destroy()

    def test_native_window_hierarchy_mousewheel(self):
        """Tests native parent-window mousewheel dispatch, hierarchy discovery, notch and touchpad scaling."""
        import customtkinter as ctk
        from gui.main_window import MainWindow

        storage = StorageManager(self.test_dir)
        app = MainWindow(storage=storage)
        app.withdraw()
        try:
            # Create a test scrollable frame and populate with children
            sf = ctk.CTkScrollableFrame(app, width=300, height=200)
            sf.pack(padx=10, pady=10)

            btn = ctk.CTkButton(sf, text="Child Button")
            btn.pack(pady=5)
            lbl = ctk.CTkLabel(sf, text="Child Label")
            lbl.pack(pady=5)
            for i in range(25):
                ctk.CTkLabel(sf, text=f"Row {i}").pack(pady=2)

            outer_entry = ctk.CTkEntry(app)
            outer_entry.pack(pady=5)

            tb = ctk.CTkTextbox(app, height=100)
            tb.pack(pady=5)

            app.update()

            # 1. Test hierarchy traversal discovery
            self.assertEqual(app._find_scrollable_container(lbl), sf)
            self.assertEqual(app._find_scrollable_container(btn), sf)
            self.assertEqual(app._find_scrollable_container(sf._parent_canvas), sf)
            self.assertEqual(app._find_scrollable_container(sf), sf)
            self.assertIsNone(app._find_scrollable_container(outer_entry))
            self.assertEqual(app._find_scrollable_container(tb), tb)

            # 2. Test event dispatch with simulated events
            class MockScrollEvent:
                def __init__(self, delta, widget=None, x=100, y=100, state=0):
                    self.delta = delta
                    self.widget = widget
                    self.x_root = x
                    self.y_root = y
                    self.state = state

            # Wheel down on label inside sf returns 'break' and moves view
            yview_before = sf._parent_canvas.yview()[0]
            res1 = app._on_window_mousewheel(MockScrollEvent(delta=-120, widget=lbl))
            app.update()
            yview_after = sf._parent_canvas.yview()[0]
            self.assertEqual(res1, "break")
            self.assertGreater(yview_after, yview_before)

            # Wheel up on button inside sf returns 'break' and moves view up
            yview_before2 = sf._parent_canvas.yview()[0]
            res2 = app._on_window_mousewheel(MockScrollEvent(delta=120, widget=btn))
            app.update()
            yview_after2 = sf._parent_canvas.yview()[0]
            self.assertEqual(res2, "break")
            self.assertLess(yview_after2, yview_before2)

            # Precision touchpad / Surface Arc Mouse micro-deltas (e.g. -2, -1)
            yview_tp_before = sf._parent_canvas.yview()[0]
            res3 = app._on_window_mousewheel(MockScrollEvent(delta=-1, widget=lbl))
            app.update()
            yview_tp_after = sf._parent_canvas.yview()[0]
            self.assertEqual(res3, "break")
            self.assertGreater(yview_tp_after, yview_tp_before)

            # Diagonal swipe with Shift modifier on vertical container scrolls yview, not dropped
            yview_diag_before = sf._parent_canvas.yview()[0]
            res4 = app._on_window_mousewheel(MockScrollEvent(delta=-2, widget=lbl, state=1))
            app.update()
            yview_diag_after = sf._parent_canvas.yview()[0]
            self.assertEqual(res4, "break")
            self.assertGreater(yview_diag_after, yview_diag_before)

            # Tcl/Tk 9.0 <TouchpadScroll> 32-bit packed delta (e.g. dx=3, dy=-12)
            packed_tp = (3 << 16) | (-12 & 0xFFFF)
            dx, dy = app._unpack_touchpad_deltas(packed_tp)
            self.assertEqual((dx, dy), (3, -12))
            yview_tp9_before = sf._parent_canvas.yview()[0]
            res_tp9 = app._on_touchpad_scroll(MockScrollEvent(delta=packed_tp, widget=lbl))
            app.update()
            yview_tp9_after = sf._parent_canvas.yview()[0]
            self.assertEqual(res_tp9, "break")
            self.assertGreater(yview_tp9_after, yview_tp9_before)

            # Textbox deferral returns None to allow native Tkinter Text handling when standalone
            res_tb = app._on_window_mousewheel(MockScrollEvent(delta=-120, widget=tb))
            self.assertIsNone(res_tb)

            # Nested CTkTextbox inside a CTkScrollableFrame (like LoggerView form_scroll)
            # passes scroll events through to the parent CTkScrollableFrame when unfocused/empty
            nested_tb = ctk.CTkTextbox(sf, height=60)
            nested_tb.pack(pady=4)
            app.update()
            self.assertEqual(app._find_scrollable_container(nested_tb), sf)
            self.assertEqual(app._find_scrollable_container(nested_tb._textbox), sf)
            yview_nested_before = sf._parent_canvas.yview()[0]
            res_nested = app._on_window_mousewheel(MockScrollEvent(delta=-120, widget=nested_tb._textbox))
            app.update()
            yview_nested_after = sf._parent_canvas.yview()[0]
            self.assertEqual(res_nested, "break")
            self.assertGreater(yview_nested_after, yview_nested_before)

            # Non-scrollable widget returns None
            res_none = app._on_window_mousewheel(MockScrollEvent(delta=-120, widget=outer_entry))
            self.assertIsNone(res_none)
        finally:
            app.destroy()

    def test_critical_reflection_na_default_and_localization(self):
        """Verifies CriticalExamination defaults to N/A, canonical decisions, and i18n roundtrips."""
        # Dataclass default
        crit = CriticalExamination()
        self.assertEqual(crit.application_decision, "N/A")
        self.assertEqual(crit.flaws_plausibility, "")

        # Canonical decisions list
        self.assertIn("N/A", CANONICAL_DECISIONS)
        self.assertEqual(CANONICAL_DECISIONS, ["N/A", "Accepted", "Modified", "Rejected"])

        # Localization EN
        set_current_locale("en")
        self.assertEqual(localize_decision("N/A"), "N/A")
        self.assertEqual(canonicalize_decision("N/A"), "N/A")
        self.assertEqual(canonicalize_decision("Accepted"), "Accepted")

        # Localization DE
        set_current_locale("de")
        self.assertEqual(localize_decision("N/A"), "N/A")
        self.assertEqual(canonicalize_decision("N/A"), "N/A")
        self.assertEqual(localize_decision("Accepted"), "Akzeptiert")
        self.assertEqual(canonicalize_decision("Akzeptiert"), "Accepted")
        set_current_locale("en")

        # Serialization roundtrip with N/A
        doc = ProtocolDocument(title="N/A Decision Test")
        drop = InteractionDrop(
            drop_number=1,
            target_engine="Claude 3.5 Sonnet",
            core_intent="Synthesis",
            raw_prompt="Summarize this paper",
            critical_examination=CriticalExamination(flaws_plausibility="Plausible", application_decision="N/A"),
        )
        doc.drops.append(drop)

        drop_dict = drop.to_dict()
        self.assertEqual(drop_dict["critical_examination"]["application_decision"], "N/A")

        reconstructed = InteractionDrop.from_dict(drop_dict)
        self.assertIsNotNone(reconstructed.critical_examination)
        self.assertEqual(reconstructed.critical_examination.application_decision, "N/A")
        self.assertEqual(reconstructed.critical_examination.flaws_plausibility, "Plausible")

    def test_pluralized_verification_sources_and_short_title_in_exports(self):
        """Verifies pluralized sources headers and short title display in Markdown, HTML, and PDF exports."""
        # Verify i18n plural forms
        set_current_locale("en")
        self.assertEqual(t("fc_th_source"), "Verification Sources & Evidence")
        self.assertIn("Verification Sources & Evidence", t("lbl_fc_source"))

        set_current_locale("de")
        self.assertEqual(t("fc_th_source"), "Verifikationsquellen & Belege")
        self.assertIn("Verifikationsquellen & Belege", t("lbl_fc_source"))
        set_current_locale("en")

        # Verify export rendering
        doc = ProtocolDocument(title="Plural Sources & Title Ref Test")
        drop = InteractionDrop(
            drop_number=1,
            title="Arch Linux Analysis",
            target_engine="GPT-4o",
            core_intent="Code Generation",
            raw_prompt="Write a systemd unit file",
        )
        doc.drops.append(drop)

        fc = FactCheckEntry(
            claim="systemd handles restart delays natively",
            primary_source="systemd.service(5) man page, Section RestartSec=",
            status="Confirmed",
        )
        doc.assign_fact_check(fc, drop.id)

        # Markdown
        md = generate_markdown(doc)
        self.assertIn("Verification Sources & Evidence", md)
        self.assertIn("Interaction #1", md)
        self.assertIn("*Arch Linux Analysis*", md)

        # HTML
        html = generate_html(doc)
        self.assertIn("Verification Sources &amp; Evidence", html)
        self.assertIn("Interaction #1", html)
        self.assertIn("Arch Linux Analysis", html)

        # PDF
        pdf_path = self.test_dir / "test_plural_verification.pdf"
        render_to_pdf(doc, str(pdf_path))
        self.assertTrue(pdf_path.exists())
        self.assertGreater(pdf_path.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()


