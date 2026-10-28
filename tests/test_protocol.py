"""
Automated unit and integration tests for Academic AI Protocol Logger core engine.
Tests serialization, Markdown compilation, HTML generation, and PDF rendering.
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
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
)


class TestProtocolEngine(unittest.TestCase):
    def setUp(self):
        self.doc = ProtocolDocument(
            title="Test Master Thesis AI Protocol",
            metadata=ProtocolMetadata(
                student_name="Sven Várszegi, B.A.",
                degree_program="Master Digital Business Management (FH OÖ / JKU)",
                course_code_title="DBM-900: Master Thesis Colloquium",
                assignment_scope="Master's Thesis",
                examiner="Prof. Dr. Barbara Krumay",
                submission_date="2026-09-24",
                primary_ai_models="Claude 3.5 Sonnet, Gemini 1.5 Pro",
                secondary_ai_models="NotebookLM",
            )
        )

        drop1 = InteractionDrop(
            drop_number=1,
            timestamp="2026-09-24 14:30 CEST",
            target_engine="Claude 3.5 Sonnet",
            context_scope="Literature Review PDF (Smith et al. 2023)",
            core_intent="Synthesis",
            raw_prompt="Synthesize the key challenges of decentralized AI agent coordination.",
            raw_output="The primary challenges include asynchronous state synchronization and adversarial Byzantine fault tolerance.",
            critical_examination=CriticalExamination(
                flaws_plausibility="Verified against Smith (2023) section 3. The claim about 99.9% tolerance is exaggerated. Corrected in draft.",
                application_decision="Modified",
            ),
            fact_checks=[
                FactCheckEntry(
                    claim="Smith (2023) demonstrated 99.9% Byzantine resilience in 100-node networks.",
                    primary_source="Smith (2023), Section 3.2, p. 18",
                    status="Refuted",
                    rectification_note="Actual empirical result was 87.4% under latency stress.",
                )
            ]
        )
        self.doc.drops.append(drop1)

    def test_json_serialization(self):
        json_str = self.doc.to_json()
        loaded = ProtocolDocument.from_json(json_str)

        self.assertEqual(loaded.title, self.doc.title)
        self.assertEqual(loaded.metadata.student_name, "Sven Várszegi, B.A.")
        self.assertEqual(len(loaded.drops), 1)
        self.assertEqual(loaded.drops[0].core_intent, "Synthesis")
        self.assertEqual(loaded.drops[0].critical_examination.application_decision, "Modified")
        self.assertEqual(len(loaded.drops[0].fact_checks), 1)
        self.assertEqual(loaded.drops[0].fact_checks[0].status, "Refuted")

    def test_markdown_generation(self):
        md = generate_markdown(self.doc)
        self.assertIn("# Generative AI Documentation & Verification Protocol", md)
        self.assertIn("Sven Várszegi, B.A.", md)
        self.assertIn("Master Digital Business Management (FH OÖ / JKU)", md)
        self.assertIn("### Section A: Chronological Interaction Protocol", md)
        self.assertIn("### Section B: Claim & Source Verification Matrix", md)
        self.assertIn("[Refuted]", md)
        self.assertIn("```text", md)

    def test_html_generation(self):
        html_doc = generate_html(self.doc)
        self.assertIn("<!DOCTYPE html>", html_doc)
        self.assertIn("Sven Várszegi, B.A.", html_doc)
        self.assertIn("pill-modified", html_doc)
        self.assertIn("badge-refuted", html_doc)
        self.assertIn("Arial", html_doc)

    def test_pdf_rendering(self):
        output_pdf = Path(__file__).parent / "test_protocol.pdf"
        try:
            res_path = render_to_pdf(self.doc, str(output_pdf))
            self.assertTrue(output_pdf.exists())
            self.assertGreater(output_pdf.stat().st_size, 1000, "PDF should be non-empty")
            print(f"\nPDF generated successfully at: {res_path} ({output_pdf.stat().st_size} bytes)")
        finally:
            if output_pdf.exists():
                output_pdf.unlink()

    def test_complex_multipage_pdf_rendering(self):
        """Verifies that large multi-page prompts, Unicode box drawings, and code blocks render flawlessly via ReportLab."""
        doc = ProtocolDocument(title="Complex Multi-Page & Box Drawing Test")
        complex_output = (
            "### Pipeline Architecture\n\n"
            "[ Client Request ]\n"
            "       │\n"
            "       ▼\n"
            "[ API Gateway / Load Balancer ]\n"
            "       │\n"
            "       ├───► [ Auth & Ingestion Service (gRPC) ]\n"
            "       │            │\n"
            "       │            ▼\n"
            "       │     [ Kafka Event Bus ]\n"
            "       │            ├───► [ State Worker (Idempotent) ] ──► [ Primary DB ]\n"
            "       │            └───► [ Verification Node ] ──► [ Audit Store ]\n\n"
            "### Mathematical Formula & Long Output\n"
            "Benchmark latency under synthetic loads exceeding $2.5\\times$ expected volume.\n\n"
            "```python\n"
            "def process_transaction(payload):\n"
            "    # Multi-line code block simulation\n"
            + "\n".join([f"    step_{i} = do_work_{i}()" for i in range(120)])
            + "\n    return True\n```"
        )
        doc.drops.append(InteractionDrop(
            target_engine="Google Gemini",
            context_scope="Data Test",
            core_intent="Method Check",
            raw_prompt="Deep architecture query with math $CAP$ and ASCII diagrams",
            raw_output=complex_output,
        ))

        output_pdf = Path(__file__).parent / "test_complex.pdf"
        try:
            res_path = render_to_pdf(doc, str(output_pdf))
            self.assertTrue(output_pdf.exists())
            self.assertGreater(output_pdf.stat().st_size, 10000)
            from pypdf import PdfReader
            reader = PdfReader(str(output_pdf))
            self.assertGreaterEqual(len(reader.pages), 2, "Complex output should span multiple pages cleanly")
        finally:
            if output_pdf.exists():
                output_pdf.unlink()


if __name__ == "__main__":
    unittest.main()

