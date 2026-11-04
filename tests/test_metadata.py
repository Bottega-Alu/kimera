"""Regression checks for lossless metadata boundaries and the real PDF path."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import fitz

SCRIPT = Path(__file__).resolve().parents[1] / "skills/kimera/scripts/render.py"
spec = importlib.util.spec_from_file_location("kimera_render", SCRIPT)
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)


class MetadataTests(unittest.TestCase):
    def test_unknown_opening_line_survives(self):
        source = "Nota: pagamento entro 7 giorni\n\nImporto: 42 EUR\n"
        body, meta, _ = render.markdown_to_html(source)
        self.assertEqual(meta, {})
        self.assertIn("Nota: pagamento entro 7 giorni", body)
        self.assertIn("Importo: 42 EUR", body)

    def test_known_metadata_stops_at_body(self):
        body, meta, _ = render.markdown_to_html(
            "Title: Documento\nLang: it\nNota: conservare\n    Dettaglio originale\n")
        self.assertEqual(meta, {"title": "Documento", "lang": "it"})
        self.assertIn("Nota: conservare", body)
        self.assertIn("Dettaglio originale", body)

    def test_duplicate_is_preserved(self):
        body, meta, _ = render.markdown_to_html("Title: Primo\nTitle: Secondo\n")
        self.assertEqual(meta["title"], "Primo")
        self.assertIn("Title: Secondo", body)

    def test_leading_blank_escapes_known_key(self):
        body, meta, _ = render.markdown_to_html("\nTitle: testo letterale\n")
        self.assertEqual(meta, {})
        self.assertIn("Title: testo letterale", body)

    def test_bom_and_crlf(self):
        body, meta, _ = render.markdown_to_html("\ufeffTitle: Titolo\r\n\r\nCorpo\r\n")
        self.assertEqual(meta, {"title": "Titolo"})
        self.assertIn("Corpo", body)

    def test_opening_note_reaches_pdf(self):
        with tempfile.TemporaryDirectory(prefix="kimera-metadata-") as temp:
            source = Path(temp) / "sample.md"
            source.write_text("Nota: pagamento entro 7 giorni\n\nImporto: 42 EUR\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(source),
                "--verify", "--json"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertIn("not exact text fidelity", report["verification_scope"])
            self.assertEqual(report["visual_review"], "not performed by renderer")
            with fitz.open(report["pdf"]) as pdf:
                text = " ".join(page.get_text() for page in pdf)
            self.assertIn("Nota: pagamento entro 7 giorni", text)
            self.assertIn("Importo: 42 EUR", text)


if __name__ == "__main__":
    unittest.main()
