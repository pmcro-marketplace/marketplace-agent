import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skills.marketplace.scripts import catalog_cycle
from skills.marketplace.scripts.trail import PHASE_FILES, Trail


@unittest.skipUnless(os.name == "posix", "Private trail storage requires POSIX")
class CatalogCycleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        home = Path(temporary.name)
        self.project = home / ".pmcro/projects/test-catalog"
        for directory in (self.project.parent.parent, self.project.parent, self.project):
            directory.mkdir(mode=0o700)
        home_patch = patch.object(Path, "home", return_value=home)
        home_patch.start()
        self.addCleanup(home_patch.stop)

    def test_run_and_reopen_ten_correlated_private_frames(self):
        trail, passed = catalog_cycle.run(self.project.name)
        self.assertTrue(passed)
        reopened = Trail(self.project.name, trail.id)
        _, frames = reopened.verified_files()
        self.assertEqual(len([name for name in frames if name.endswith(".jsonl")]), 10)
        self.assertEqual(reopened.directory.stat().st_mode & 0o777, 0o700)
        self.assertTrue(all(path.stat().st_mode & 0o777 == 0o600 for path in reopened.directory.iterdir()))
        evidence = catalog_cycle.verify(reopened)
        self.assertEqual((evidence["catalogs"], evidence["memberships"], evidence["routes"]), (4, 10, 23))
        self.assertEqual(evidence["provider_invocation"], "NOT_INVOKED")
        self.assertEqual(evidence["approval"], "NOT_ISSUED")

    def test_tamper_rejected_and_existing_frame_not_overwritten(self):
        trail, passed = catalog_cycle.run(self.project.name)
        self.assertTrue(passed)
        with self.assertRaises(ValueError):
            trail.put(PHASE_FILES["input"], {})
        (trail.directory / PHASE_FILES["input"]).write_text("{}")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            catalog_cycle.verify(Trail(self.project.name, trail.id))

    @patch.object(catalog_cycle, "discover", return_value=[])
    def test_false_discovery_preserves_rejected_trail(self, _):
        trail, passed = catalog_cycle.run(self.project.name)
        self.assertFalse(passed)
        seal, _ = Trail(self.project.name, trail.id).verified_files()
        self.assertEqual(seal["disposition"], "reject")
        with self.assertRaisesRegex(ValueError, "not accepted"):
            catalog_cycle.verify(Trail(self.project.name, trail.id))

    def test_no_registry_entry_is_created(self):
        with self.assertRaises(FileNotFoundError):
            catalog_cycle.run("unregistered")
        self.assertFalse((self.project.parent / "unregistered").exists())
