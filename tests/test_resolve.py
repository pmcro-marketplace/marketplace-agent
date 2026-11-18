import unittest
import subprocess
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from skills.marketplace.scripts import read_adapters, resolve
from skills.marketplace.scripts.resolve import DOCTOR, DOCTOR_SOURCE, discover, select, reviewed_files, doctor
from skills.marketplace.scripts.read_adapters import LIST, PROJECT, invoke_list, invoke_project

ROOT = Path(__file__).resolve().parent / "fixtures"
route = partial(resolve.route, project_id="marketplace-fixture")


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        self.rows = discover(ROOT)
        self.row = select(self.rows, "project-management", "dotagents-agent", "dotagents", "doctor")
        self.resolved = {**self.row, "resolution": "RESOLVED_SOURCE"}
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name).resolve()
        home = patch.object(Path, "home", return_value=self.project / "home")
        scope = self.project / "home" / ".pmcro" / "projects" / "marketplace-fixture"
        scope.mkdir(parents=True)
        for path in (scope, scope.parent, scope.parent.parent):
            path.chmod(0o700)
        home.start()
        self.addCleanup(home.stop)
        (self.project / "agents.toml").touch()
        self.checkouts = {DOCTOR_SOURCE["repository"]: self.project}

    def test_all_catalog_membership_routes(self):
        self.assertEqual(len(self.rows), 23)
        self.assertEqual(len({(r["marketplace"], r["address"]) for r in self.rows}), 23)
        self.assertEqual(sum(r["adapter"] == "dotagents-doctor" for r in self.rows), 1)
        self.assertEqual(sum(r["adapter"] != "HOST_ADAPTER_REQUIRED" for r in self.rows), 3)

    def test_exact_agent_identity(self):
        with self.assertRaises(ValueError):
            select(self.rows, "project-management", "project-agent", "dotagents", "doctor")

    def test_handoff_preserves_prompt(self):
        raw = ' {"operation":"check"}\n'
        receipt = route(self.row, raw, {}, self.project)
        self.assertEqual(receipt["handoff"]["from"], "marketplace:resolver")
        self.assertEqual(receipt["handoff"]["chain"], [{"skill": DOCTOR, "prompt": raw}])
        self.assertEqual(receipt["invocation"], "NOT_INVOKED")

    @patch.object(resolve, "doctor")
    def test_no_grant_means_no_call(self, provider):
        receipt = route(self.resolved, '{"operation":"check"}', self.checkouts, self.project, True)
        self.assertEqual(receipt["status"], "BLOCKED")
        self.assertEqual(receipt["reason"], "EXACT_OPERATOR_GRANT_REQUIRED")
        provider.assert_not_called()

    @patch.object(resolve, "doctor")
    def test_trail_storage_failure_prevents_call(self, provider):
        with self.assertRaises(resolve.TrailWriteError):
            route(self.resolved, '{"operation":"check"}', self.checkouts, self.project,
                  True, [DOCTOR], project_id="unregistered")
        provider.assert_not_called()

    @patch.object(resolve, "doctor")
    def test_no_mutating_operation(self, provider):
        for prompt in ('{"operation":"check","fix":true}', '{"operation":"fix"}', '{"operation":"check","apply":true}'):
            self.assertEqual(route(self.resolved, prompt, self.checkouts, self.project, True, [DOCTOR])["status"], "BLOCKED")
        provider.assert_not_called()

    @patch.object(resolve, "doctor")
    def test_disabled_and_unresolved_are_denied(self, provider):
        for row in (self.row, {**self.resolved, "enabled": False}, {**self.resolved, "adapter": "HOST_ADAPTER_REQUIRED"}):
            self.assertEqual(route(row, '{"operation":"check"}', self.checkouts, self.project, True, [DOCTOR])["status"], "BLOCKED")
        provider.assert_not_called()

    @patch.object(resolve, "doctor")
    def test_scope_must_be_absolute_and_initialized(self, provider):
        for project in (None, Path("."), self.project / "missing"):
            self.assertEqual(route(self.resolved, '{"operation":"check"}', self.checkouts, project, True, [DOCTOR])["status"], "BLOCKED")
        provider.assert_not_called()

    @patch.object(resolve, "doctor", return_value={"status": "READY_FOR_HANDOFF", "invocation": "NOT_INVOKED"})
    def test_dry_run_never_requests_execution(self, provider):
        result = route(self.resolved, '{"operation":"check"}', self.checkouts, self.project)
        self.assertEqual(result["status"], "READY_FOR_HANDOFF")
        provider.assert_called_once_with(self.project, self.project, False)

    @patch.object(resolve, "doctor")
    def test_host_skill_not_equated_with_execution(self, provider):
        row = select(self.rows, "plugin-creation", "plugin-agent", "plugin-creator", "create-plugin")
        row = {**row, "resolution": "RESOLVED_HOST"}
        result = route(row, '{}', {}, self.project, True, [row["address"]])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["invocation"], "NOT_INVOKED")
        self.assertEqual(result["reason"], "HOST_ADAPTER_REQUIRED")
        provider.assert_not_called()

    @patch.object(resolve, "git", return_value="unreviewed bytes")
    def test_reviewed_integrity_denial(self, _git):
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            reviewed_files(self.project)

    @patch.object(resolve, "reviewed_files", return_value={"skills/doctor/scripts/run.py": b"reviewed"})
    @patch.object(resolve.shutil, "which", return_value="/local/dotagents")
    @patch.object(resolve.subprocess, "run", return_value=subprocess.CompletedProcess([], 0,
           stdout=b"private path\nAll checks passed.\nProvider exit: 0\n", stderr=b"private stderr"))
    def test_receipt_redacts_raw_provider_output(self, call, _which, _files):
        result = doctor(self.project, self.project, True)
        self.assertEqual(result["status"], "PASS")
        self.assertNotIn("private", str(result))
        self.assertEqual(result["provider_exit"], 0)
        self.assertNotIn("--fix", call.call_args.args[0])
        self.assertNotIn("--apply", call.call_args.args[0])

    @patch.object(resolve, "invoke_list")
    def test_list_exact_grant_and_operation(self, provider):
        row = {**select(self.rows, "project-management", "dotagents-agent", "dotagents", "list"), "resolution": "RESOLVED_SOURCE"}
        for prompt, grant in [('{"operation":"list"}', [DOCTOR]), ('{"operation":"install"}', [LIST]), ('{"operation":"list","global":true}', [LIST])]:
            self.assertEqual(route(row, prompt, self.checkouts, self.project, True, grant)["status"], "BLOCKED")
        provider.assert_not_called()
        provider.return_value = {"status": "PASS", "invocation": "INVOKED"}
        self.assertEqual(route(row, '{"operation":"list"}', self.checkouts, self.project, True, [LIST])["status"], "PASS")
        provider.assert_called_once_with(self.project, self.project, True)

    @patch.object(resolve, "invoke_project")
    def test_lifecycle_mutations_denied(self, provider):
        row = {**select(self.rows, "project-management", "project-agent", "projects", "project-lifecycle"), "resolution": "RESOLVED_SOURCE"}
        for operation in ("register", "init", "activate", "archive", "start"):
            self.assertEqual(route(row, '{"operation":"'+operation+'"}', self.checkouts, self.project, True, [PROJECT])["status"], "BLOCKED")
        provider.assert_not_called()
        provider.return_value = {"status": "READY_FOR_HANDOFF", "invocation": "NOT_INVOKED"}
        self.assertEqual(route(row, '{"operation":"status"}', self.checkouts, self.project)["status"], "READY_FOR_HANDOFF")
        provider.assert_called_once_with(self.project, self.project, "marketplace-fixture", None, "status", None, False)

    @patch.object(read_adapters, "materialize")
    @patch.object(read_adapters.shutil, "which", return_value="/local/dotagents")
    @patch.object(read_adapters.subprocess, "run", return_value=subprocess.CompletedProcess([], 0,
        stdout=b'Invoke: dotagents --project list\n{"skills":[{"name":"private-name"}],"plugins":[]}\nProvider exit: 0\n'))
    def test_list_receipt_redacts_names(self, call, _which, _materialize):
        result = invoke_list(self.project, self.project, True)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["skill_count"], 1)
        self.assertNotIn("private-name", str(result))
        self.assertIn("--json", call.call_args.args[0])

    def test_project_scope_rejects_overlap_and_invalid_id(self):
        for identifier, state in [("../escape", self.project), ("demo", self.project), ("demo", Path("."))]:
            with self.assertRaises(ValueError):
                invoke_project(self.project, self.project, identifier, state, "status", None, False)

    @patch.object(read_adapters, "materialize")
    @patch.object(read_adapters.subprocess, "run")
    @patch.object(read_adapters.runpy, "run_path")
    def test_runtime_denies_unreviewed_binding(self, load, execute, _materialize):
        with TemporaryDirectory() as state:
            load.return_value = {"RESERVED": set(), "absolute": lambda p: p, "private_dir": lambda p: None,
                                 "read_record": lambda p, i: {"project_root": str(self.project),
                                      "configuration": {"adapter": "/unknown", "sha256": "unreviewed"}}}
            with self.assertRaises(ValueError):
                invoke_project(self.project, self.project, "demo", Path(state), "runtime", Path("/unknown"), True)
            execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
