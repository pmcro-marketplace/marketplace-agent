import json
import shutil
import tempfile
import unittest
from pathlib import Path

from skills.marketplace.scripts.validate_catalogs import DOMAINS, parse, validate, pairs

ROOT = Path(__file__).resolve().parent / "fixtures"


class MarketplaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / "marketplaces", self.root / "marketplaces")

    def tearDown(self):
        self.tmp.cleanup()

    def edit(self, domain, change):
        path = self.root / "marketplaces" / domain / "marketplace.yaml"
        data = parse(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def test_four_catalogs_and_no_false_resolution(self):
        rows = validate(self.root)
        self.assertEqual({row["marketplace"] for row in rows}, DOMAINS)
        self.assertEqual(len(rows), 10)
        self.assertTrue(all(row["resolution"].endswith("REQUIRED") for row in rows))

    def test_selected_catalog(self):
        rows = validate(self.root, selected="template-generation")
        self.assertEqual([row["plugin"] for row in rows], ["template"])

    def test_host_discovery_is_explicit(self):
        rows = validate(self.root, host={"project": ["project"]}, selected="project-management")
        resolved = [r for r in rows if r["resolution"] == "RESOLVED_HOST"]
        self.assertEqual([r["plugin"] for r in resolved], ["project"])
        self.assertEqual(sum(r["resolution"] == "SOURCE_DISCOVERY_REQUIRED" for r in rows), 2)

    def test_duplicate_membership_denied(self):
        self.edit("skill-creation", lambda d: d["plugins"].append(d["plugins"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate member"):
            validate(self.root)

    def test_unpinned_source_denied(self):
        self.edit("template-generation", lambda d: d["plugins"][0]["source"].update(ref="main"))
        with self.assertRaisesRegex(ValueError, "unpinned"):
            validate(self.root)

    def test_traversal_denied(self):
        self.edit("template-generation", lambda d: d["plugins"][0]["source"].update(path="../template"))
        with self.assertRaisesRegex(ValueError, "invalid package path"):
            validate(self.root)

    def test_wrong_catalog_location_denied(self):
        self.edit("project-management", lambda d: d["source"].update(repository="other/repo"))
        with self.assertRaisesRegex(ValueError, "invalid catalog locator"):
            validate(self.root)

    def test_duplicate_fields_and_arguments_denied(self):
        with self.assertRaisesRegex(ValueError, "duplicate field"):
            parse('{"name":"first","name":"second"}')
        with self.assertRaisesRegex(ValueError, "duplicate argument"):
            pairs(["plugin=skill", "plugin=other"])


if __name__ == "__main__":
    unittest.main()
