from pathlib import Path
import json, sys

root = Path(__file__).resolve().parents[1]
required = [
    root / "SKILL.md",
    root / "references" / "contract.md",
    root / "references" / "creation-contract.md",
    root / "assets" / "request.json",
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    print("FAIL: missing " + ", ".join(missing))
    sys.exit(1)

req = json.loads((root / "assets" / "request.json").read_text(encoding="utf-8"))
if req.get("function") != "create-marketplace":
    print("FAIL: creator request function")
    sys.exit(1)
if req.get("source", {}).get("type") not in {"github-repository", "local-repository", "remote-repository"}:
    print("FAIL: unsupported source type")
    sys.exit(1)

print("PASS: creator")
sys.exit(0)
