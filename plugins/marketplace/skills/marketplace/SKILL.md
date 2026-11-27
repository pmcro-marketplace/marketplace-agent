---
name: marketplace
description: Marketplace catalog subagent for discovery, source attachment, plugin membership, validation, synchronization, listing, removal, and publication.
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
Supported identities:

- `/marketplace:marketplace:discover`
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
See `references/contract.md`, `references/catalog-contract.md`, `references/source-types.md`, `assets/request.json`, and `assets/marketplace.example.yaml`.


## Script reference

Scripts are not loaded into context. An agent runs one only when a step needs it, and you can run the same command by hand from this skill's folder.

| Script | Purpose | Manual run |
|---|---|---|
| `scripts/validate.py` | Structural self-check: verifies the skill's required files (and request.json contents where applicable). Takes no arguments; prints `PASS: <skill>` and exits 0, or prints `FAIL: ...` and exits 1. | `python scripts/validate.py` |
