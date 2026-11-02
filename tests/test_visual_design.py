"""Non-regression guards for the accepted visual structure and responsive design."""
from pathlib import Path
from html.parser import HTMLParser
import unittest

ROOT = Path(__file__).resolve().parents[1]
H = (ROOT / "index.html").read_text("utf-8")
C = (ROOT / "design-v2.css").read_text("utf-8")
A = (ROOT / "acquire/index.html").read_text("utf-8")

class DesignV2(unittest.TestCase):
    def test_visual_structure(self):
        for text in ("hero-copy", "flow-visual", "flow-mobile", "impact-svg", "application-grid", "identity-band", "closing-buttons"):
            self.assertIn(text, H)
        self.assertIn("INTELLIGENCE", H)
        self.assertIn("Data", H)
        self.assertIn("Compute", H)
        self.assertIn("Models", H)
        self.assertIn("Discovery", H)
    def test_accessible_and_responsive(self):
        self.assertIn('aria-labelledby="outrushhero-title outrushhero-desc"', H)
        self.assertIn("prefers-reduced-motion:reduce", C)
        self.assertIn("@media(max-width:540px)", C)
        self.assertIn("pointer:coarse", C)
        self.assertIn("aria-label=", H)
    def test_no_leaked_pricing(self):
        for content in (H, A, C):
            for word in ("5,000", "5000", "14,888", "14888", "Buy Now"):
                self.assertNotIn(word, content)
    def test_shared_design_system(self):
        self.assertIn('href="/design-v2.css"', H)
        self.assertIn('href="/design-v2.css"', A)
        self.assertIn('class="concept-v2"', H)
        self.assertIn('class="acquire-v2"', A)

if __name__ == "__main__":
    unittest.main()
