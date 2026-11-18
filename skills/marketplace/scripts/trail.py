"""Private, write-once PMCR-O trail frames for the local marketplace bridge."""
import hashlib
import json
import os
import re
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

if __package__:
    from .validate_catalogs import parse, require
else:
    from validate_catalogs import parse, require

PHASE_FILES = {
    "startup": "00-startup.jsonl", "input": "00-input.jsonl",
    "orchestrate": "00-orchestrate.jsonl", "plan": "01-plan.jsonl",
    "make": "01-make.jsonl", "check": "01-check.jsonl", "reflect": "01-reflect.jsonl",
}
TERMINAL = {"PASS", "FAIL", "BLOCKED", "READY_FOR_HANDOFF", "UNVERIFIED"}
PROJECT_ID = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?\Z")
MAX_FRAME = 256 * 1024


def now():
    return datetime.now(timezone.utc).isoformat()


def private(path, *, create=False, directory=True):
    if create:
        path.mkdir(mode=0o700, exist_ok=True)
    meta = path.lstat()
    valid_type = stat.S_ISDIR(meta.st_mode) if directory else stat.S_ISREG(meta.st_mode) and meta.st_nlink == 1
    require(valid_type and meta.st_uid == os.getuid() and not (meta.st_mode & 0o077),
            "Trail path must be private, owned by the operator and not a link")
    return path


def project_trails(project_id, create=False):
    require(os.name == "posix", "Private trail storage requires POSIX permissions")
    require(isinstance(project_id, str) and PROJECT_ID.fullmatch(project_id) and "--" not in project_id,
            "Valid private trail project ID required")
    root = Path.home().resolve() / ".pmcro"
    project = root / "projects" / project_id
    for path in (root, root / "projects", project):
        private(path)
    # Never create a project in the registry. Only Project Agent owns that.
    return private(project / "trails", create=create)


def new_id():
    return str(uuid4())


def valid_id(value):
    require(isinstance(value, str) and str(UUID(value, version=4)) == value, "Invalid trail UUID")
    return value


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Trail:
    def __init__(self, project_id, trail_id=None):
        parent = project_trails(project_id, create=trail_id is None)
        self.id = new_id() if trail_id is None else valid_id(trail_id)
        self.directory = parent / self.id
        if trail_id is None:
            self.directory.mkdir(mode=0o700)
            sync_directory(parent)
        private(self.directory)
        self.writable = trail_id is None

    def put(self, name, value):
        require(self.writable and not (self.directory / "disposition.json").exists(), "Trail is sealed or read-only")
        require(isinstance(name, str) and Path(name).name == name, "Invalid frame filename")
        data = (json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True) + "\n").encode("utf-8")
        require(len(data) <= MAX_FRAME, "Trail frame exceeds size limit")
        fd, temp = tempfile.mkstemp(prefix=".frame-", dir=self.directory)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            # Atomic publication without replacing an existing frame.
            os.link(temp, self.directory / name, follow_symlinks=False)
        finally:
            os.unlink(temp)
        sync_directory(self.directory)

    def raw(self, name):
        require(isinstance(name, str) and Path(name).name == name, "Invalid frame filename")
        with private(self.directory / name, directory=False).open("rb") as stream:
            data = stream.read(MAX_FRAME + 1)
        require(len(data) <= MAX_FRAME, "Trail frame exceeds size limit")
        return data

    def read(self, name):
        return parse(self.raw(name).decode("utf-8"))

    def begin(self, phase, route, intent, inputs, parent=None):
        span = {"kind": "PmcroTrailFrame", "version": 1, "trail_id": self.id,
                "frame_id": new_id(), "parent_id": parent, "phase": phase, "route": route,
                "intent": intent, "inputs": inputs, "started_at": now(), "status": "STARTED"}
        self.put(f"{span['frame_id']}.start.json", span)
        return span

    def end(self, span, status, outcome, evidence):
        require(status in TERMINAL, "Invalid terminal status")
        name = PHASE_FILES.get(span["phase"], f"{span['frame_id']}.jsonl")
        self.put(name, {**span, "status": status, "finished_at": now(), "outcome": outcome, "evidence": evidence})
        return name

    def phase(self, name):
        return self.read(PHASE_FILES[name])

    def seal(self, disposition):
        require(disposition in {"accept", "reject", "needs-approval"}, "Invalid disposition")
        files = {p.name: hashlib.sha256(self.raw(p.name)).hexdigest() for p in self.directory.iterdir()}
        require(files, "Cannot seal an empty trail")
        self.put("disposition.json", {"trail_id": self.id, "final_cycle": "01", "sealed_at": now(),
                                      "disposition": disposition, "files": files})
        self.writable = False

    def verified_files(self):
        seal = self.read("disposition.json")
        require(seal["trail_id"] == self.id and seal["final_cycle"] == "01", "Seal does not match trail")
        require(set(seal["files"]) == {p.name for p in self.directory.iterdir()} - {"disposition.json"},
                "Trail file inventory mismatch")
        files = {}
        for name, digest in seal["files"].items():
            raw = self.raw(name)
            require(hashlib.sha256(raw).hexdigest() == digest, "Trail frame digest mismatch")
            files[name] = parse(raw.decode("utf-8"))
        for name, frame in files.items():
            if name == "00-frame.json" or name.endswith(".start.json"):
                continue
            identifier = valid_id(frame["frame_id"])
            start = files[f"{identifier}.start.json"]
            require(name == PHASE_FILES.get(frame["phase"], f"{identifier}.jsonl"), "Frame filename mismatch")
            require(frame["trail_id"] == self.id and frame["status"] in TERMINAL and
                    start == {**{k: v for k, v in frame.items() if k not in {"outcome", "evidence", "finished_at"}},
                              "status": "STARTED"}, "Frame lifecycle mismatch")
            parent = frame["parent_id"]
            require(parent is None or (parent != identifier and f"{valid_id(parent)}.start.json" in files),
                    "Frame parent missing")
        require({name for name in files if name.endswith(".start.json")} ==
                {f"{frame['frame_id']}.start.json" for name, frame in files.items() if name.endswith(".jsonl")},
                "Incomplete invocation in sealed trail")
        return seal, files
