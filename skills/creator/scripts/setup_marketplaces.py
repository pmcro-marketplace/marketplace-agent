"""Marketplace Agent: scaffold the federated marketplace from a declared plan."""
import argparse
import json
import sys
import tempfile
from pathlib import Path

if __package__:
    from ...marketplace.scripts.validate_catalogs import DOMAINS, REPOSITORY, parse, require, validate
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "marketplace" / "scripts"))
    from validate_catalogs import DOMAINS, REPOSITORY, parse, require, validate

STARTER = Path(__file__).resolve().parents[1] / "assets" / "setup-plan.json"
SETUP = {"agent": "marketplace-agent", "plugin": "marketplace", "skill": "creator",
         "address": "/marketplace:creator:setup", "function": "setup"}


def setup(root, plan=STARTER, *, apply=False):
    require(root.is_absolute() and root == root.resolve(strict=True) and root.is_dir(),
            "An existing canonical, absolute target directory is required")
    with plan.open("rb") as stream:
        raw = stream.read(262145)
    require(len(raw) <= 262144, "Setup plan exceeds size limit")
    data = parse(raw.decode("utf-8"))
    require(isinstance(data, dict) and set(data) == {"kind", "version", "catalogs"} and
            data["kind"] == "MarketplaceSetup" and type(data["version"]) is int and data["version"] == 1 and
            isinstance(data["catalogs"], dict) and set(data["catalogs"]) == DOMAINS, "Invalid marketplace setup plan")
    files = {}
    for name, members in sorted(data["catalogs"].items()):
        rel = f"marketplaces/{name}/marketplace.yaml"
        files[rel] = {"kind": "Marketplace", "version": 1, "name": name,
                      "source": {"type": "github-repository", "repository": REPOSITORY, "path": rel},
                      "plugins": members}
    # Validate the entire blueprint using Marketplace Agent before touching the target.
    with tempfile.TemporaryDirectory(prefix="pmcro-marketplace-plan-") as directory:
        staged = Path(directory)
        for rel, value in files.items():
            path = staged / rel
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        validate(staged)
        if apply:
            # Publish only in a trusted operator workspace, never over an
            # existing file or directory. Roll back files created by this call
            # on ordinary I/O failure. Do not retry over crash leftovers.
            created = []
            destination = root / "marketplaces"
            destination.mkdir(mode=0o755)
            created.append((destination, True))
            try:
                for rel in files:
                    path = root / rel
                    path.parent.mkdir()
                    created.append((path.parent, True))
                    with path.open("xb") as stream:
                        created.append((path, False))
                        stream.write((staged / rel).read_bytes())
                validate(root)
            except (OSError, ValueError, TypeError, KeyError, RecursionError):
                for path, directory_created in reversed(created):
                    try:
                        path.rmdir() if directory_created else path.unlink()
                    except OSError:
                        pass
                raise
    return {"status": "PASS" if apply else "READY_FOR_HANDOFF", "changed": apply, "catalogs": list(files),
            "provider_invocation": "NOT_INVOKED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True, help="Existing workspace directory")
    parser.add_argument("--plan", type=Path, default=STARTER, help="MarketplaceSetup JSON; defaults to the bundled starter")
    parser.add_argument("--apply", action="store_true", help="Explicitly grant local folder and manifest creation")
    args = parser.parse_args()
    try:
        print(json.dumps(setup(args.target, args.plan, apply=args.apply), indent=2))
        return 0
    except FileExistsError:
        print(json.dumps({"status": "BLOCKED", "reason": "Existing marketplace destination was not overwritten"}))
        return 1
    except (ValueError, OSError, TypeError, KeyError, RecursionError):
        print(json.dumps({"status": "BLOCKED", "reason": "Plan or workspace is invalid; inspect before retrying"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
