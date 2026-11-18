import importlib.util, json, tempfile, unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"skills"/"marketplace"/"scripts"/"project_catalogs.py"
spec=importlib.util.spec_from_file_location("project_catalogs",SCRIPT)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

class CatalogProjectionTests(unittest.TestCase):
    def fixture(self):
        return {
          "kind":"Marketplace","version":1,"name":"demo","displayName":"Demo",
          "owner":{"name":"Owner"},"source":{"type":"github-repository","repository":"acme/catalog"},
          "plugins":[
            {"name":"b","repository":"acme/b","description":"B","category":"Developer Tools","enabled":True},
            {"name":"a","repository":"acme/a","description":"A","category":"Developer Tools","enabled":True}
          ]
        }

    def test_copilot_and_claude_shape_uses_github_sources(self):
        out=mod.github_catalog(self.fixture())
        self.assertEqual([p["name"] for p in out["plugins"]],["a","b"])
        self.assertEqual(out["plugins"][0]["source"],{"source":"github","repo":"acme/a","ref":"main"})

    def test_codex_shape_has_policy_and_category(self):
        item=mod.codex_catalog(self.fixture())["plugins"][0]
        self.assertEqual(item["source"]["source"],"url")
        self.assertEqual(item["policy"]["installation"],"AVAILABLE")
        self.assertIn("category",item)

    def test_cursor_is_explicitly_not_representable(self):
        self.assertEqual(mod.status_catalog()["cursor"]["status"],"NOT_REPRESENTABLE")

    def test_duplicate_plugin_name_is_invalid(self):
        data=self.fixture(); data["plugins"].append(dict(data["plugins"][0],repository="acme/c"))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"marketplace.yaml"; p.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaises(ValueError): mod.load(p)

if __name__=="__main__": unittest.main()
