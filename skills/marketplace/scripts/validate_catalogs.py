"""Marketplace Agent: validate the authored catalogs and optional immutable sources.

Only reads Git objects and explicit host-discovery evidence; never installs or invokes a skill.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

REPOSITORY = "pmcro-marketplace/Everything-as-Agent"
DOMAINS = {"project-management", "template-generation", "skill-creation", "plugin-creation"}
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def valid_name(value):
    return isinstance(value, str) and NAME.fullmatch(value) is not None


def parse(raw):
    # JSON syntax is a strict subset of YAML 1.2. Reject duplicate fields.
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate field: {key}")
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError(f"invalid JSON constant: {value}")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)


def git(checkout, *args):
    return subprocess.run(["git", "--no-replace-objects", "-C", str(checkout), *args], check=True,
                          text=True, encoding="utf-8", capture_output=True, timeout=20).stdout


def verify_git_member(source, name, skills, checkout):
    repository = source["repository"]
    ref = source["ref"]
    origin = git(checkout, "remote", "get-url", "origin").strip()
    require(origin in {f"https://github.com/{repository}.git", f"https://github.com/{repository}"},
            f"origin mismatch for {name}")
    require(git(checkout, "rev-parse", f"{ref}^{{commit}}").strip() == ref, f"commit mismatch for {name}")
    prefix = "" if source["path"] == "." else f"{source['path']}/"
    manifest = parse(git(checkout, "show", f"{ref}:{prefix}plugin.json"))
    require(manifest["name"] == name, f"plugin identity mismatch: {name}")
    for skill in skills:
        front = git(checkout, "show", f"{ref}:{prefix}skills/{skill}/SKILL.md").split("---", 2)
        require(len(front) == 3 and re.search(rf"(?m)^name:\s*{re.escape(skill)}\s*$", front[1]),
                f"skill identity mismatch: {name}/{skill}")


def validate(root, checkouts=None, host=None, selected=None, *, include_routes=False):
    checkouts = checkouts or {}
    host = host or {}
    base = root / "marketplaces"
    require(base.is_dir() and not base.is_symlink(), "expected a real marketplaces directory")
    catalogs = sorted(base.glob("*/marketplace.yaml"))
    require({p.parent.name for p in catalogs} == DOMAINS, "expected four unique domain catalogs")
    require(selected is None or selected in DOMAINS, "unknown marketplace")
    for name, skills in host.items():
        require(valid_name(name) and isinstance(skills, list) and all(valid_name(s) for s in skills), "invalid host inventory")
        require(len(skills) == len(set(skills)), "duplicate host skill")
    findings = []
    for path in catalogs:
        require(not path.parent.is_symlink() and not path.is_symlink() and path.is_file(),
                "expected a real catalog file")
        with path.open("rb") as stream:
            raw = stream.read(262145)
        require(len(raw) <= 262144, "catalog exceeds 256 KiB")
        data = parse(raw.decode("utf-8"))
        domain = path.parent.name
        require(data["kind"] == "Marketplace" and type(data["version"]) is int and data["version"] == 1 and data["name"] == domain,
                f"invalid catalog identity: {domain}")
        require(data["source"] == {"type": "github-repository", "repository": REPOSITORY,
                                  "path": path.relative_to(root).as_posix()}, f"invalid catalog locator: {domain}")
        members = data["plugins"]
        require(isinstance(members, list) and members, f"empty catalog: {domain}")
        seen = set()
        for member in members:
            name, skills, source = member["name"], member["skills"], member["source"]
            require(valid_name(name) and name not in seen, f"invalid/duplicate member: {domain}/{name}")
            seen.add(name)
            require(valid_name(member["agent"]) and type(member["enabled"]) is bool, "invalid agent or enabled flag")
            require(isinstance(skills, list) and skills and all(valid_name(s) for s in skills) and len(set(skills)) == len(skills),
                    f"invalid skills: {name}")
            if source["type"] == "github-plugin":
                require(set(source) == {"type", "repository", "ref", "path"}, "unexpected GitHub source fields")
                require(REPO.fullmatch(source["repository"]) and SHA.fullmatch(source["ref"]), f"invalid source or unpinned ref: {name}")
                require(source["path"] in {".", f"plugins/{name}"}, f"invalid package path: {name}")
                checkout = checkouts.get(source["repository"])
                status = "SOURCE_DISCOVERY_REQUIRED"
                if checkout is not None and (selected is None or selected == domain):
                    verify_git_member(source, name, skills, checkout)
                    status = "RESOLVED_SOURCE"
            elif source["type"] == "installed-plugin":
                require(source == {"type": "installed-plugin", "name": name}, f"invalid host reference: {name}")
                status = "RESOLVED_HOST" if set(skills).issubset(host.get(name, [])) else "HOST_DISCOVERY_REQUIRED"
            else:
                raise ValueError(f"unsupported provider source: {source['type']}")
            if selected is None or selected == domain:
                row = {"marketplace": domain, "plugin": name, "skills": skills,
                       "enabled": member["enabled"], "resolution": status}
                if include_routes:
                    row.update(agent=member["agent"], source=source)
                findings.append(row)
    return findings


def pairs(values):
    result = {}
    for value in values:
        key, sep, val = value.partition("=")
        require(sep and key and val and key not in result, f"invalid/duplicate argument: {key}")
        result[key] = val
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog-root", type=Path, required=True)
    parser.add_argument("--marketplace", choices=sorted(DOMAINS))
    parser.add_argument("--checkout", action="append", default=[], metavar="OWNER/REPO=PATH")
    parser.add_argument("--host", action="append", default=[], metavar="PLUGIN=SKILL,SKILL",
                        help="Fresh host-discovered skills; not an authorization or execution receipt")
    parser.add_argument("--require-resolution", action="store_true")
    args = parser.parse_args()
    try:
        findings = validate(args.catalog_root.resolve(), pairs(args.checkout),
                            {k: v.split(",") for k, v in pairs(args.host).items()}, args.marketplace)
        unresolved = [f for f in findings if f["enabled"] and f["resolution"].endswith("REQUIRED")]
        print(json.dumps({"catalog_validation": "PASS", "provider_resolution": "BLOCKED" if unresolved else "PASS",
                          "invocation": "NOT_INVOKED", "memberships": findings}, indent=2))
        return 1 if args.require_resolution and unresolved else 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError, subprocess.SubprocessError) as exc:
        print(json.dumps({"catalog_validation": "FAIL", "invocation": "NOT_INVOKED",
                          "error_type": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
