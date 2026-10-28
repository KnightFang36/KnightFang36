"""Check the factual data boundaries and the portable SVG output."""
import contextlib
from copy import deepcopy
from datetime import datetime, timezone
from io import StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_profile as profile


def repo(name="Example", **overrides):
    value = dict(name=name, fork=False, private=False, archived=False,
                 disabled=False, size=100, language="Python",
                 html_url=f"https://github.com/{profile.USERNAME}/{name}",
                 pushed_at="2026-10-01T10:00:00Z")
    value.update(overrides)
    return value


class DataTests(unittest.TestCase):
    def test_excludes_forks_private_archived_disabled_empty_and_profile(self):
        values = [repo("Include"), repo("Fork", fork=True),
                  repo("Private", private=True), repo("Archive", archived=True),
                  repo("Disabled", disabled=True), repo("Empty", size=0),
                  repo(profile.USERNAME.lower())]
        with patch.object(profile, "github_get", side_effect=[values, {"Python": 120}]) as get:
            data = profile.fetch_snapshot()
        self.assertEqual([r["name"] for r in data["repositories"]], ["Include"])
        self.assertEqual(get.call_count, 2)
        self.assertEqual(data["updated_at"], datetime.now(timezone.utc).date().isoformat())

    def test_fetches_next_page_instead_of_silently_truncating(self):
        first_page = [repo(f"Fork{i}", fork=True) for i in range(100)]
        with patch.object(profile, "github_get", side_effect=[first_page, [repo()], {"Go": 50}]) as get:
            data = profile.fetch_snapshot()
        self.assertEqual(len(data["repositories"]), 1)
        self.assertIn("page=2", get.call_args_list[1].args[0])

    def test_byte_weighting_and_other_preserve_the_total(self):
        values = [dict(languages={"Python": 100, "Go": 20, "HTML": 5}),
                  dict(languages={"Python": 100, "Go": 20, "CSS": 4,
                                  "Shell": 3, "TypeScript": 10})]
        shares = profile.language_shares(values)
        self.assertEqual(shares[0], ("Python", 200))
        self.assertEqual(shares[-1], ("Other", 7))
        self.assertEqual(sum(n for _, n in shares), 262)

    def test_api_failure_keeps_the_previous_snapshot_and_artwork(self):
        with TemporaryDirectory() as directory:
            snapshot = Path(directory) / "profile.json"
            assets = Path(directory) / "assets"
            assets.mkdir()
            artwork = assets / "signal-dark.svg"
            snapshot.write_text("previous snapshot")
            artwork.write_text("previous artwork")
            error = HTTPError("https://api.github.com", 403, "Rate limited", {}, None)
            with patch.object(profile, "SNAPSHOT", snapshot), \
                 patch.object(profile, "ASSETS", assets), \
                 patch.object(profile, "fetch_snapshot", side_effect=error), \
                 patch.object(sys, "argv", ["build_profile.py", "--refresh"]), \
                 contextlib.redirect_stderr(StringIO()):
                self.assertEqual(profile.main(), 1)
            self.assertEqual(snapshot.read_text(), "previous snapshot")
            self.assertEqual(artwork.read_text(), "previous artwork")

    def test_rejects_negative_and_non_integer_byte_counts(self):
        data = json.loads(profile.SNAPSHOT.read_text())
        for bad_value in [-1, 1.5, True]:
            invalid = deepcopy(data)
            invalid["repositories"][0]["languages"] = {"Python": bad_value}
            with self.subTest(value=bad_value), self.assertRaises(ValueError):
                profile.build(invalid)

    def test_rejects_a_profile_or_duplicate_project_in_the_snapshot(self):
        data = json.loads(profile.SNAPSHOT.read_text())
        invalid = deepcopy(data)
        invalid["repositories"][0]["name"] = profile.USERNAME
        with self.assertRaises(ValueError):
            profile.build(invalid)
        data["repositories"].append(deepcopy(data["repositories"][0]))
        with self.assertRaises(ValueError):
            profile.build(data)


class ArtworkTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(profile.SNAPSHOT.read_text())

    def test_all_theme_and_viewport_variants_are_valid_self_contained_svg(self):
        files = profile.build(self.data)
        self.assertEqual(len(files), 8)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        for path, content in files.items():
            with self.subTest(asset=path.name):
                root = ET.fromstring(content)
                self.assertIsNotNone(root.find("svg:title", ns))
                self.assertIsNotNone(root.find("svg:desc", ns))
                self.assertFalse(root.findall(".//svg:script", ns))
                self.assertFalse(root.findall(".//svg:foreignObject", ns))
                self.assertFalse(root.findall(".//svg:image", ns))
                self.assertNotIn("@import", content)
                if path.name.startswith("hero"):
                    self.assertIn("prefers-reduced-motion: reduce", content)

    def test_empty_projects_and_zero_bytes_do_not_invent_activity(self):
        self.data["repositories"] = []
        content = profile.render_signal(self.data, "dark")
        ET.fromstring(content)
        self.assertIn("00 original public projects", content)
        self.assertIn("No source-language data yet.", content)
        self.assertNotIn("nan", content.lower())
        self.assertNotIn("%<", content)

    def test_dynamic_text_is_xml_escaped(self):
        self.data["repositories"][0]["language"] = 'C & C++ <language>'
        content = profile.render_signal(self.data, "light", mobile=True)
        ET.fromstring(content)
        self.assertIn("C &amp; C++ &lt;language&gt;", content)

    def test_checked_in_artwork_matches_the_snapshot(self):
        for path, content in profile.build(self.data).items():
            with self.subTest(asset=path.name):
                self.assertEqual(path.read_text(), content)


if __name__ == "__main__":
    unittest.main()
