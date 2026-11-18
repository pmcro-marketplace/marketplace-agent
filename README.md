# Marketplace Agent

Canonical repository: `pmcro-marketplace/marketplace-agent`.

## Identity

```text
Agent:        @marketplace-agent
Plugin:       marketplace
Skill/Subagent:
  marketplace
  creator
Function:     concrete marketplace operation
```

Marketplace Agent owns marketplace catalogs and marketplace membership. It does **not** author plugin packages.

- Plugin Agent creates or updates plugin packages.
- Marketplace Agent creates the marketplace/catalog and adds existing plugins to it.
- GitHub Agent performs GitHub repository operations when the marketplace source type is `github-repository`.
- Hook Agent may surround applicable calls only when a real lifecycle runtime/provider exists.

## Authored source and generated projections

The root `marketplace.yaml` is the single authored marketplace source. Host compatibility catalogs are generated under `dist/` and must not be edited by hand.

```text
marketplace.yaml
  -> dist/.github/plugin/marketplace.json
  -> dist/.claude-plugin/marketplace.json
  -> dist/.agents/plugins/marketplace.json
  -> dist/projection-status.json
```

Run:

```bash
python skills/marketplace/scripts/project_catalogs.py
python skills/marketplace/scripts/project_catalogs.py --check
```

The projector emits GitHub-source catalogs for Copilot/Claude and Git URL entries with explicit install/auth policy for Codex. Cursor remains explicitly `NOT_REPRESENTABLE` for this cross-repository topology until a matching documented source form is verified.

## Marketplace source types

```text
github-repository
local-repository
remote-repository
```

A GitHub repository is a marketplace **source/container type**, not the plugin itself.

## Functions

```text
@marketplace-agent /create-marketplace
@marketplace-agent /discover
@marketplace-agent /add-source
@marketplace-agent /add-plugin
@marketplace-agent /remove-plugin
@marketplace-agent /list-plugins
@marketplace-agent /validate
@marketplace-agent /sync
@marketplace-agent /publish
```

See `INVOCATION.md` for exact internal capability identities and `skills/marketplace/references/catalog-contract.md` for the catalog contract.
