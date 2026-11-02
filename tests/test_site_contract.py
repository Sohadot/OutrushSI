"""Static contract tests for the Outrush.si presentation site.

Run with: python3 -m unittest discover -s tests -v
No third-party packages or network access are needed.
"""
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "index.html").read_text(encoding="utf-8")
ACQUIRE = (ROOT / "acquire/index.html").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
ROBOTS = (ROOT / "robots.txt").read_text(encoding="utf-8")
SITEMAP = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
LLMS = (ROOT / "llms.txt").read_text(encoding="utf-8")


class LinkInspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.anchors = []
        self.scripts = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a":
            self.anchors.append(attrs.get("href", ""))
        if tag == "script":
            self.scripts.append(attrs)


class SiteContract(unittest.TestCase):
    def test_html_structure(self):
        for html in (HOME, ACQUIRE):
            self.assertTrue(html.lower().startswith("<!doctype html>"))
            self.assertTrue(html.rstrip().endswith("</html>"))
            self.assertIn('lang="en"', html)
            self.assertIn('name="viewport"', html)
            self.assertIn('class="skip-link"', html)

    def test_internal_links_resolve(self):
        parsed = LinkInspector()
        parsed.feed(HOME)
        for href in parsed.anchors:
            if href.startswith("#"):
                self.assertIn(href[1:], parsed.ids, msg=href)
            if href == "/acquire/":
                self.assertTrue((ROOT / "acquire/index.html").exists())
        self.assertIn("/acquire/", parsed.anchors)

    def test_acquisition_only_accepts_proposals(self):
        self.assertIn("https://www.dynadot.com/fr/market/user-listings/outrush.si", ACQUIRE)
        self.assertIn("mailto:agent@sohadot.com", ACQUIRE)
        self.assertIn("Escrow.com", ACQUIRE)
        self.assertIn("All offers remain subject to review and acceptance", ACQUIRE)
        for html in (HOME, ACQUIRE):
            self.assertNotRegex(html, r"(?i)buy\s*now|minimum\s*offer|instant\s*checkout")
            self.assertNotRegex(html, r"\$\s*\d+|\b(?:5000|5,000|14888|14,888)\b")

    def test_home_is_timeless_and_no_fake_product(self):
        self.assertNotIn("wave", HOME.lower())
        self.assertNotIn("domain investors", HOME.lower())
        self.assertIn("not existing Outrush products", HOME)
        for word in ("Data", "Compute", "Models", "INTELLIGENCE", "Decisions", "Agents", "Systems", "Discovery"):
            self.assertIn(word, HOME)

    def test_citations_and_schema(self):
        for host in ("merriam-webster.com/dictionary/outrush", "collinsdictionary.com/dictionary/english/outrush", "dictionary.com/browse/outrush", "register.si"):
            self.assertIn(host, HOME)
        schema = re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', HOME, re.S)
        self.assertIsNotNone(schema)
        data = json.loads(schema.group(1))
        types = [x["@type"] for x in data["@graph"]]
        self.assertIn("WebPage", types)
        self.assertIn("DefinedTerm", types)
        self.assertNotIn("Product", types)
        self.assertNotIn("Organization", types)

    def test_indexing_and_canonical(self):
        self.assertIn('name="robots" content="index, follow"', HOME)
        self.assertIn('name="robots" content="noindex, follow"', ACQUIRE)
        self.assertIn('href="https://outrush.si/"', HOME)
        self.assertIn('href="https://outrush.si/acquire/"', ACQUIRE)
        tree = ElementTree.fromstring(SITEMAP)
        urls = [e.text for e in tree.iter() if e.tag.endswith("loc")]
        self.assertEqual(urls, ["https://outrush.si/"])
        self.assertNotIn("Disallow: /acquire", ROBOTS)

    def test_accessibility_and_runtime(self):
        self.assertIn('aria-labelledby="flow-title flow-desc"', HOME)
        self.assertIn('class="flow-mobile"', HOME)
        self.assertIn("prefers-reduced-motion:reduce", CSS)
        self.assertIn("a:focus-visible", CSS)
        self.assertNotIn("https://fonts.googleapis.com", HOME + CSS)
        parsed = LinkInspector()
        parsed.feed(HOME)
        self.assertEqual([s.get("src") for s in parsed.scripts if s.get("src")], ["/script.js"])

    def test_link_preview_cards(self):
        expected = [
            'property="og:image" content="https://outrush.si/assets/social-card.jpg"',
            'property="og:image:width" content="1200"',
            'property="og:image:height" content="630"',
            'name="twitter:card" content="summary_large_image"',
            'name="twitter:image" content="https://outrush.si/assets/social-card.jpg"',
        ]
        for html in (HOME, ACQUIRE):
            for entry in expected:
                self.assertIn(entry, html)
        self.assertIn('property="og:url" content="https://outrush.si/"', HOME)
        self.assertIn('property="og:url" content="https://outrush.si/acquire/"', ACQUIRE)

    def test_llms_truthfulness(self):
        self.assertIn("not an operating company", LLMS)
        self.assertIn("not the domain's official meaning", LLMS)
        self.assertIn("https://outrush.si/acquire/", LLMS)


if __name__ == "__main__":
    unittest.main()
