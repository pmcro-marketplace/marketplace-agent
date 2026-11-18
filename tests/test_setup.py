import json
import tempfile
import unittest
from pathlib import Path

from skills.creator.scripts.setup_marketplaces import STARTER, setup
from skills.marketplace.scripts.resolve import discover
from skills.marketplace.scripts.validate_catalogs import DOMAINS, parse, validate

ROOT = Path(__file__).resolve().parent / "fixtures"


class MarketplaceSetupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def test_manual_preview_leaves_workspace_empty(self):
        result = setup(self.root)
        self.assertEqual(result["status"], "READY_FOR_HANDOFF")
        self.assertFalse(result["changed"])
        self.assertFalse(any(self.root.iterdir()))

    def test_setup_builds_all_catalogs_and_resolves_23_routes(self):
        result = setup(self.root, apply=True)
        self.assertTrue(result["changed"])
        self.assertEqual(result["provider_invocation"], "NOT_INVOKED")
        self.assertEqual(len(validate(self.root)), 10)
        self.assertEqual(len(discover(self.root)), 23)
        for domain in DOMAINS:
            path = Path("marketplaces") / domain / "marketplace.yaml"
            self.assertEqual(parse((self.root / path).read_text()), parse((ROOT / path).read_text()))

    def test_existing_and_linked_destinations_are_untouched(self):
        target = self.root / "marketplaces"
        target.mkdir()
        with self.assertRaises(FileExistsError):
            setup(self.root, apply=True)
        self.assertEqual(list(target.iterdir()), [])
        target.rename(self.root / "other")
        target.symlink_to(self.root / "other", target_is_directory=True)
        with self.assertRaises(FileExistsError):
            setup(self.root, apply=True)
        self.assertTrue(target.is_symlink())
        self.assertEqual(list(target.iterdir()), [])

    def test_invalid_plan_cannot_create_partial_destination(self):
        plan = parse(STARTER.read_text())
        plan["catalogs"]["template-generation"][0]["source"]["ref"] = "main"
        spec = self.root / "invalid.json"
        spec.write_text(json.dumps(plan))
        with self.assertRaises(ValueError):
            setup(self.root, spec, apply=True)
        self.assertFalse((self.root / "marketplaces").exists())


if __name__ == "__main__":
    unittest.main()
