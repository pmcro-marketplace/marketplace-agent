from pathlib import Path
import json, sys

root = Path(__file__).resolve().parents[1]
required = [
    root / "SKILL.md",
    root / "references" / "contract.md",
    root / "references" / "catalog-contract.md",
    root / "references" / "source-types.md",
    root / "assets" / "request.json",
    root / "assets" / "marketplace.example.yaml",
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    print("FAIL: missing " + ", ".join(missing))
    sys.exit(1)

req = json.loads((root / "assets" / "request.json").read_text(encoding="utf-8"))
if req.get("plugin") != "marketplace" or req.get("skill") != "marketplace":
    print("FAIL: invalid request identity")
    sys.exit(1)

print("PASS: marketplace")
sys.exit(0)
