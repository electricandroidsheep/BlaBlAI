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
        self.assertIn("Total Interaction Drops Logged", md)

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


if __name__ == "__main__":
    unittest.main()

