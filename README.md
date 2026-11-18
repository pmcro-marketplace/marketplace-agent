# Marketplace Agent

Canonical repository: `pmcro-marketplace/marketplace-agent`.

## Standalone setup and acceptance

The packaged skills own local catalog setup, validation, discovery and guarded resolution. See the [standalone runbook](skills/marketplace/references/standalone-runbook.md) for manual commands, read-only provider grants and private trail verification. No Everything-as-Agent checkout or separate engine folder is required for local catalog setup and verification.

```sh
python3 -B -m unittest discover -s tests -v
```

The Marketplace Checker workflow uses a catalog-only fixture. It does not dispatch external providers, install plugins, approve pull requests, or publish catalogs. Its Reflector result is a redacted job summary, not a human decision.

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
@marketplace-agent /setup
@marketplace-agent /discover
@marketplace-agent /resolve
@marketplace-agent /add-source
@marketplace-agent /add-plugin
@marketplace-agent /remove-plugin
@marketplace-agent /list-plugins
@marketplace-agent /validate
@marketplace-agent /sync
@marketplace-agent /publish
```

See `INVOCATION.md` for exact internal capability identities and `skills/marketplace/references/catalog-contract.md` for the catalog contract.
