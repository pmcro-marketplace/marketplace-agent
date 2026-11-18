"""Run or reopen the standalone, catalog-only PMCR-O acceptance cycle."""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from skills.creator.scripts.setup_marketplaces import SETUP, STARTER, setup
from skills.marketplace.scripts.resolve import RESOLVER, discover
from skills.marketplace.scripts.trail import PHASE_FILES, Trail
from skills.marketplace.scripts.validate_catalogs import DOMAINS, require, validate

INTENT = "Set up, validate and discover marketplace catalogs in a fresh local workspace."
EXPECTED = {"plugin-creation": (3, 6), "project-management": (3, 12),
            "skill-creation": (3, 3), "template-generation": (1, 2)}
FUNCTIONS = {
    "setup": SETUP,
    "validate": {**RESOLVER, "function": "validate", "address": "/marketplace:marketplace:validate"},
    "discover": {**RESOLVER, "function": "discover", "address": "/marketplace:marketplace:discover"},
}


def phase_route(phase):
    return {"implementation": "catalog_cycle.py", "function": phase, "host_skill_invoked": False}


def observe(trail, phase, route, parent, inputs, fn, *, context=False):
    span = trail.begin(phase, route, INTENT, inputs, parent)
    try:
        evidence = fn(span["frame_id"]) if context else fn()
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
        trail.end(span, "FAIL", {"error_type": type(exc).__name__}, {})
        raise
    trail.end(span, "PASS", {"invocation": "INVOKED"}, evidence)
    return span["frame_id"]


def proof(trail, make, frames):
    ids = make["evidence"]
    require(set(ids) == set(FUNCTIONS), "Unexpected catalog functions")
    observations = {}
    for key, route in FUNCTIONS.items():
        frame = frames[f"{ids[key]}.jsonl"]
        require(frame["phase"] == "function" and frame["parent_id"] == make["frame_id"]
                and frame["route"] == route and frame["status"] == "PASS"
                and frame["outcome"] == {"invocation": "INVOKED"}
                and frame["inputs"] == {"mode": "catalog-only"}
                and frame["trail_id"] == trail.id, "Catalog function receipt mismatch")
        observations[key] = frame["evidence"]
    scaffold, validation, discovery = (observations[name] for name in FUNCTIONS)
    expected_files = [f"marketplaces/{name}/marketplace.yaml" for name in sorted(DOMAINS)]
    require(scaffold == {"status": "PASS", "changed": True, "catalogs": expected_files,
                         "provider_invocation": "NOT_INVOKED"}, "Scaffold did not match expected layout")
    counts = {name: sum(item["marketplace"] == name for item in validation) for name in DOMAINS}
    route_counts = {name: sum(item["marketplace"] == name for item in discovery) for name in DOMAINS}
    require(all((counts[name], route_counts[name]) == EXPECTED[name] for name in DOMAINS)
            and len(validation) == sum(counts.values()) and len(discovery) == sum(route_counts.values()),
            "Catalog membership or route counts drifted")
    resolved = {(item["marketplace"], item["plugin"]): item["skills"] for item in validation}
    routes = {(item["marketplace"], item["plugin"], item["skill"]) for item in discovery}
    require(len(resolved) == len(validation) and len(routes) == len(discovery)
            and routes == {(domain, plugin, skill) for (domain, plugin), skills in resolved.items() for skill in skills},
            "Discovery does not match the validated memberships")
    require(all(row["resolution"] in {"SOURCE_DISCOVERY_REQUIRED", "HOST_DISCOVERY_REQUIRED"}
                for row in validation + discovery), "Catalog-only cycle cannot claim external resolution")
    return {"catalogs": len(counts), "memberships": len(validation), "routes": len(discovery),
            "provider_invocation": "NOT_INVOKED", "host_installation": "NOT_TESTED"}


def run(project_id):
    trail = Trail(project_id)
    run_span = trail.begin("orchestrate", phase_route("orchestrate"), INTENT, {"mode": "catalog-only"})
    parent = run_span["frame_id"]

    def phase(name, fn, inputs=None, *, context=False):
        return observe(trail, name, phase_route(name), parent, inputs or {}, fn, context=context)

    def make_catalog(make_id):
        with tempfile.TemporaryDirectory(prefix="pmcro-catalog-") as directory:
            workspace = Path(directory).resolve()
            operations = (lambda: setup(workspace, apply=True), lambda: validate(workspace),
                          lambda: discover(workspace))
            return {name: observe(trail, "function", FUNCTIONS[name], make_id,
                                  {"mode": "catalog-only"}, fn)
                    for name, fn in zip(FUNCTIONS, operations)}

    try:
        startup = phase("startup", lambda: {"starter_sha256": hashlib.sha256(STARTER.read_bytes()).hexdigest()})
        admitted = phase("input", lambda: {"external_providers_allowed": False}, {"after": startup})
        plan = phase("plan", lambda: {"functions": [row["address"] for row in FUNCTIONS.values()]},
                     {"after": admitted})
        make = phase("make", make_catalog, {"after": plan}, context=True)
        check = phase("check", lambda: proof(trail, trail.phase("make"),
                      {p.name: trail.read(p.name) for p in trail.directory.glob("*.jsonl")}), {"after": make})
        phase("reflect", lambda: {"verdict": "ACCEPT", "approval": "NOT_ISSUED"}, {"after": check})
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        trail.end(run_span, "FAIL", {"disposition": "reject"}, {})
        trail.seal("reject")
        return trail, False
    trail.end(run_span, "PASS", {"disposition": "accept"}, {})
    trail.seal("accept")
    return trail, True


def verify(trail):
    seal, frames = trail.verified_files()
    require(seal["disposition"] == "accept", "Cycle was not accepted")
    orchestrate = frames[PHASE_FILES["orchestrate"]]
    require(orchestrate["inputs"] == {"mode": "catalog-only"} and orchestrate["parent_id"] is None
            and orchestrate["outcome"] == {"disposition": "accept"}, "Invalid cycle root")
    previous = None
    for name in ("startup", "input", "plan", "make", "check", "reflect", "orchestrate"):
        frame = frames[PHASE_FILES[name]]
        require(frame["intent"] == INTENT and frame["route"] == phase_route(name)
                and frame["status"] == "PASS", "Phase receipt mismatch")
        if name != "orchestrate":
            require(frame["parent_id"] == orchestrate["frame_id"]
                    and frame["inputs"] == ({"after": previous} if previous else {})
                    and frame["outcome"] == {"invocation": "INVOKED"}, "Phase correlation mismatch")
        previous = frame["frame_id"]
    make, checked, reflected = [frames[PHASE_FILES[p]] for p in ("make", "check", "reflect")]
    require(len([p for p in frames if p.endswith(".jsonl")]) == len(PHASE_FILES) + len(FUNCTIONS),
            "Unexpected extra trail frames")
    evidence = proof(trail, make, frames)
    require(checked["evidence"] == evidence and reflected["evidence"] ==
            {"verdict": "ACCEPT", "approval": "NOT_ISSUED"}, "Checker or Reflector receipt mismatch")
    return {"trail_id": trail.id, "checker": "PASS", "reflector": "ACCEPT",
            "approval": "NOT_ISSUED", **evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("run", "verify"))
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--trail-id")
    args = parser.parse_args()
    if (args.operation == "verify") != bool(args.trail_id):
        parser.error("--trail-id is required for verify and must be omitted for run")
    try:
        if args.operation == "run":
            trail, passed = run(args.project_id)
            if not passed:
                print(json.dumps({"trail_id": trail.id, "checker": "FAIL"}))
                return 1
        else:
            trail = Trail(args.project_id, args.trail_id)
        print(json.dumps(verify(Trail(args.project_id, trail.id)), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        print(json.dumps({"checker": "UNVERIFIED", "reason": "Inspect private trail state before retrying."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
