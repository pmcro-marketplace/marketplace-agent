#!/usr/bin/env python3
"""Project the canonical PMCR-O marketplace into host-specific catalogs.

marketplace.yaml is intentionally JSON-compatible YAML so this tool uses only the
Python standard library. Generated files live under dist/ and are never authoritative.

Exit codes: 0 success/in-sync, 1 drift in --check mode, 2 usage, 3 invalid canonical data.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CANONICAL = ROOT / "marketplace.yaml"
DIST = ROOT / "dist"

def load(path=CANONICAL):
    try:
        data=json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"cannot parse canonical marketplace: {exc}") from exc
    if data.get("kind")!="Marketplace" or data.get("version")!=1:
        raise ValueError("marketplace kind/version must be Marketplace/1")
    if not data.get("name") or not data.get("owner",{}).get("name"):
        raise ValueError("marketplace name and owner.name are required")
    if data.get("source",{}).get("type")!="github-repository":
        raise ValueError("this projector currently supports canonical github-repository sources")
    names=set(); repos=set()
    for item in data.get("plugins",[]):
        name=item.get("name"); repo=item.get("repository")
        if not name or not repo or "/" not in repo:
            raise ValueError("each plugin requires name and owner/repository")
        if name in names: raise ValueError(f"duplicate plugin name: {name}")
        if repo in repos: raise ValueError(f"duplicate plugin repository: {repo}")
        names.add(name); repos.add(repo)
    return data

def enabled(data):
    return sorted((p for p in data["plugins"] if p.get("enabled",True)), key=lambda p:p["name"])

def github_catalog(data):
    return {
        "name": data["name"],
        "owner": data["owner"],
        "metadata": {"description": data.get("displayName", data["name"])},
        "plugins": [
            {
                "name": p["name"],
                "description": p["description"],
                "source": {"source":"github","repo":p["repository"],"ref":"main"}
            } for p in enabled(data)
        ]
    }

def codex_catalog(data):
    return {
        "name": data["name"],
        "interface": {"displayName": data.get("displayName", data["name"])},
        "plugins": [
            {
                "name": p["name"],
                "source": {"source":"url","url":f"https://github.com/{p['repository']}.git","ref":"main"},
                "policy": {"installation":"AVAILABLE","authentication":"ON_INSTALL"},
                "category": p.get("category","Developer Tools")
            } for p in enabled(data)
        ]
    }

def status_catalog():
    return {
        "cursor": {
            "status":"NOT_REPRESENTABLE",
            "reason":"No cross-repository projection is emitted until a documented Cursor marketplace source form for this topology is verified."
        }
    }

def rendered(data):
    payloads={
      Path(".github/plugin/marketplace.json"): github_catalog(data),
      Path(".claude-plugin/marketplace.json"): github_catalog(data),
      Path(".agents/plugins/marketplace.json"): codex_catalog(data),
      Path("projection-status.json"): status_catalog(),
    }
    return {DIST/path:(json.dumps(value,indent=2,sort_keys=False)+"\n") for path,value in payloads.items()}

def project(check=False, canonical=CANONICAL):
    data=load(canonical)
    drift=[]
    for path, content in rendered(data).items():
        if check:
            if not path.exists() or path.read_text(encoding="utf-8")!=content:
                drift.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content,encoding="utf-8")
    if drift:
        print("DRIFT " + ", ".join(drift))
        return 1
    print("PASS catalog projections " + ("in sync" if check else "generated"))
    return 0

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    try: return project(check=args.check)
    except ValueError as exc:
        print(f"FAIL {exc}",file=sys.stderr); return 3

if __name__=="__main__":
    raise SystemExit(main())
