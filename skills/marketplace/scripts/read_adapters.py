"""Reviewed read-only adapters; invoke existing provider code, never emulate it."""
import hashlib
import json
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__:
    from .validate_catalogs import git, parse, require
else:
    from validate_catalogs import git, parse, require

REF = "34f893fbdd9243a1e55d46e8a04d57a7d5ca1ba1"
REPO = "shawn2024bellazan-prog/agent-skills"
LIST = "/dotagents:list"
PROJECT = "/projects:project-lifecycle"
DOTAGENTS_HASH = "4a4a7c369882e20d6c1281726ce94314df9563986aa422e58d0d4248f5811928"
LIST_FILES = {"skills/list/scripts/run.py": "c6f07e9e036678abf5ad5969e7e6deedeb862ef53936ddbd7a5237d475d750e8",
              "skills/dotagents/scripts/dotagents.py": DOTAGENTS_HASH}
PROJECT_FILES = {
    "skills/project-lifecycle/scripts/project_lifecycle.py": "248aa4703fd132de55a0f21310a4d5c180c2826903135444e6c42f7c9eefdf53",
    "skills/project-lifecycle/scripts/init.py": "6e587bc0fd0746c9d35c409817b88996c02fbefd4abe9bc3630ede8c946f08e2",
    "skills/project-lifecycle/assets/directory-template.json": "d824ee2916a6044760e17dde1de48aa1e7ac5fd4c850181643e4d61409ebe962",
}


def source(plugin):
    return {"type": "github-plugin", "repository": REPO, "ref": REF, "path": f"plugins/{plugin}"}


def materialize(checkout, plugin, hashes, base):
    for rel, expected in hashes.items():
        data = git(checkout, "show", f"{REF}:plugins/{plugin}/{rel}").encode("utf-8")
        require(hashlib.sha256(data).hexdigest() == expected, "Reviewed adapter integrity mismatch")
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def ready():
    return {"status": "READY_FOR_HANDOFF", "invocation": "NOT_INVOKED"}


def invoke_list(checkout, project, execute):
    require(shutil.which("dotagents") is not None, "DotAgents CLI unavailable")
    with tempfile.TemporaryDirectory(prefix="pmcro-list-") as directory:
        base = Path(directory)
        materialize(checkout, "dotagents", LIST_FILES, base)
        if not execute:
            return ready()
        print("@dotagents-agent -> dotagents -> list -> /dotagents:list", file=sys.stderr, flush=True)
        result = subprocess.run([sys.executable, "-I", "-B", str(base / "skills/list/scripts/run.py"),
                                 "--project", str(project), "--json"], cwd=project, stdin=subprocess.DEVNULL,
                                capture_output=True, timeout=30, check=False)
    native = re.findall(rb"(?m)^Provider exit: ([0-9]+)\r?$", result.stdout)
    code = int(native[0]) if len(native) == 1 else None
    receipt = {"status": "FAIL", "invocation": "INVOKED" if code is not None else "UNVERIFIED",
               "adapter_exit": result.returncode, "provider_exit": code,
               "stdout_sha256": hashlib.sha256(result.stdout).hexdigest()}
    if result.returncode == 0 and code == 0:
        try:
            # Exact native JSON, bounded by the wrapper's real invocation and receipt lines.
            raw = result.stdout.decode("utf-8").splitlines()
            start = raw.index("Invoke: dotagents --project list")
            end = raw.index("Provider exit: 0")
            data = parse("\n".join(raw[start + 1:end]))
            require(isinstance(data, dict) and all(isinstance(data.get(key), list) for key in ("skills", "plugins")), "Invalid list result")
            receipt.update(status="PASS", skill_count=len(data["skills"]), plugin_count=len(data["plugins"]))
        except (ValueError, TypeError, UnicodeError, KeyError):
            pass
    return receipt


def invoke_project(checkout, project, project_id, state, action, bound_adapter, execute):
    require(action in {"status", "runtime"}, "Only read-only lifecycle actions are allowed")
    require(isinstance(project_id, str) and re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?", project_id), "Invalid project ID")
    require(state is not None and state.is_absolute() and state == state.resolve(strict=True) and state.is_dir(), "Explicit private registry root required")
    require(project != state and project not in state.parents and state not in project.parents, "Project and registry must not overlap")
    with tempfile.TemporaryDirectory(prefix="pmcro-project-") as directory:
        base = Path(directory)
        materialize(checkout, "projects", PROJECT_FILES, base)
        script = base / "skills/project-lifecycle/scripts/project_lifecycle.py"
        # Reuse the pinned provider's own read-only record validation. A bound
        # runtime may call doctor, so independently admit its exact local adapter.
        provider = runpy.run_path(str(script))
        require(project_id not in provider["RESERVED"] and "--" not in project_id, "Invalid project ID")
        root = provider["absolute"](project)
        state = provider["absolute"](state)
        folder = state / "projects" / project_id
        for path in (state, state / "projects", folder):
            provider["private_dir"](path)
        record = provider["read_record"](folder / "project.json", project_id)
        require(Path(record["project_root"]) == root, "Registered project root mismatch")
        if action == "runtime" and record.get("configuration"):
            binding = record["configuration"]
            require(bound_adapter is not None and bound_adapter.is_absolute() and Path(binding["adapter"]) == bound_adapter
                    and binding["sha256"] == DOTAGENTS_HASH, "Bound adapter must be independently granted and reviewed")
            provider["verify_adapter"](binding)
            require(shutil.which("dotagents") is not None, "DotAgents CLI unavailable")
        if not execute:
            return ready()
        print(f"@project-agent -> projects -> project-lifecycle -> /projects:project-lifecycle ({action})", file=sys.stderr, flush=True)
        result = subprocess.run([sys.executable, "-I", "-B", str(script), action, "--project-id", project_id,
                                 "--project-root", str(project), "--pmcro-root", str(state)],
                                cwd=project, stdin=subprocess.DEVNULL, capture_output=True, timeout=240, check=False)
    receipt = {"status": "FAIL", "invocation": "UNVERIFIED", "adapter_exit": result.returncode,
               "stdout_sha256": hashlib.sha256(result.stdout).hexdigest()}
    try:
        data = parse(result.stdout.decode("utf-8"))
        require(isinstance(data, dict) and data.get("action") == action, "Invalid lifecycle receipt")
        receipt["invocation"] = "INVOKED"
        if (result.returncode == 0 and data.get("status") == "PASS" and data.get("changed") is False
                and data.get("runtime_started") is False and data.get("host_project_created") is False
                and data.get("project_id") == project_id and data.get("state") in {"registered", "initialized", "active", "archived"}):
            require(action != "runtime" or (data.get("memory_content_read") is False and data.get("runtime_provider") == "pmcro-private-project-registry"), "Invalid runtime receipt")
            receipt.update(status="PASS", action=action, state=data["state"], changed=False, runtime_started=False,
                           host_project_created=False)
            if action == "runtime":
                receipt.update(runtime_provider=data["runtime_provider"], memory_content_read=False,
                               scope_resolved=True)
    except (ValueError, TypeError, KeyError, UnicodeError):
        pass
    return receipt
