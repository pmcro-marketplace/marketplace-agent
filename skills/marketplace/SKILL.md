---
name: marketplace
description: "Discover, validate, and resolve marketplace catalog routes or manage plugin membership. Use for marketplace inventory, sync, or publication requests; do not author plugin packages or create marketplace containers."
---
# marketplace

## Purpose
Own marketplace catalog state after creation and keep marketplace sources, plugin membership, validation, synchronization, and publication as explicit states.

## When to Use
Use for `/discover`, `/add-source`, `/add-plugin`, `/remove-plugin`, `/list-plugins`, `/validate`, `/sync`, or `/publish`.

## When Not to Use
Do not author a plugin package; delegate that to Plugin Agent. Do not create a new marketplace container/catalog; route `/create-marketplace` to the `creator` subagent. Do not perform GitHub operations directly when GitHub Agent is available.

## Inputs
A bounded request, marketplace identity, source descriptor, authorization context, current catalog state, and evidence.

For `/add-plugin`, require:
- `marketplace_ref` — the target marketplace/catalog identity.
- `plugin_ref` — an existing plugin package identity or resolvable plugin reference.
- `enabled` — optional desired membership state; defaults to enabled when omitted.

## Deliverables
One concrete marketplace state transition or a `BLOCKED` / `NOT_INVOKED` disposition with evidence.

## Workflow
1. Resolve `@marketplace-agent` -> plugin `marketplace` -> subagent `marketplace` -> concrete function.
2. Emit the exact function identity.
3. Preserve source/container state separately from plugin membership state.
4. Delegate provider-specific operations to the narrowest real provider, such as GitHub Agent for GitHub repository sources.
5. Apply the marketplace catalog change.
6. Validate the resulting catalog and membership state.
7. Return provider evidence plus marketplace evidence.

## Validation
For the standalone PMCR-O catalogs:

- Run `python3 -B scripts/validate_catalogs.py --catalog-root /absolute/workspace` to check catalog shape. Use `--require-resolution` only when every enabled dependency must resolve.
- Run `python3 -B scripts/resolve.py discover --catalog-root /absolute/workspace` to list exact routes. For `/marketplace:marketplace:resolve`, follow `references/standalone-runbook.md` before supplying a provider checkout or execution grant. `scripts/read_adapters.py` and `scripts/trail.py` support the resolver; do not call them directly.
- Run `scripts/catalog_cycle.py` as described in the runbook for one correlated catalog-only acceptance cycle, not a provider or host invocation.

Supported identities:

- `/marketplace:marketplace:discover`
- `/marketplace:marketplace:resolve`
- `/marketplace:marketplace:add-source`
- `/marketplace:marketplace:add-plugin` — inputs: `marketplace_ref`, `plugin_ref`, optional `enabled`
- `/marketplace:marketplace:remove-plugin`
- `/marketplace:marketplace:list-plugins`
- `/marketplace:marketplace:validate`
- `/marketplace:marketplace:sync`
- `/marketplace:marketplace:publish`

A PASS requires actual marketplace/catalog evidence. A repository URL, plugin ID, emitted invocation, or installation alone is insufficient.

## Pitfalls
Emission is not invocation. Repository creation is not marketplace validation. Plugin creation is not marketplace membership. Membership is not installation. Installation is not execution.

## Resources
Read `references/contract.md` and `assets/request.json` before a membership change. Use `references/catalog-contract.md`, `references/source-types.md`, and `assets/marketplace.example.yaml` when checking a source or catalog example. Run `scripts/validate.py` for the bundled membership fixture.
