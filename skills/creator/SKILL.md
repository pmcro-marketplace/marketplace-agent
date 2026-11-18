---
name: creator
description: "Create a marketplace catalog after discovery proves a gap, or scaffold the four PMCR-O catalog folders in an existing workspace. Do not author plugin packages, attach membership, or publish repositories."
---
# creator

## Purpose
Own `/create-marketplace` and `/setup`: create marketplace catalog state without creating the plugin packages that will later be added to it.

## Local scaffold
For `/marketplace:creator:setup`, run `python3 -B scripts/setup_marketplaces.py --target /absolute/workspace` from the skill directory. The workspace must already exist and be under the operator's exclusive control. Read `assets/setup-plan.json` before changing the reviewed member set. Preview has no effect; add `--apply` only for authorized creation in a workspace without a `marketplaces/` directory. An existing destination is never overwritten. If interrupted, inspect leftovers before retrying.

## When to Use
Use for `@marketplace-agent /create-marketplace` after discovery proves the requested marketplace does not already exist in an acceptable form.

## When Not to Use
Do not author plugin packages. Do not use for adding/removing plugins from an existing marketplace. Do not simulate GitHub repository creation; delegate it to GitHub Agent.

## Inputs
Marketplace name, source type, source location or owner when applicable, visibility when applicable, initial metadata, authorization context, and acceptance criteria.

## Deliverables
A created marketplace source/container plus initialized marketplace catalog, or `BLOCKED` / `NOT_INVOKED`.

## Workflow
1. Confirm discovery evidence proves a real marketplace gap.
2. Resolve `@marketplace-agent /create-marketplace` -> `/marketplace:creator:create-marketplace`.
3. Validate `source.type`.
4. For `github-repository`, delegate repository creation to `@github-agent`; for local or remote sources, use the corresponding authorized provider.
5. Initialize the marketplace catalog contract in the source/container.
6. Validate the catalog independently from source creation.
7. Return the source evidence and catalog evidence.
8. Hand membership operations back to the `marketplace` subagent.

## Validation
Canonical function:

- `/marketplace:creator:create-marketplace`

Supported source types:

- `github-repository`
- `local-repository`
- `remote-repository`

A PASS requires both source/container evidence and a valid initialized marketplace catalog.

## Pitfalls
A repository by itself is not a marketplace. A plugin by itself is not a marketplace. Marketplace Agent creates the catalog; Plugin Agent creates plugin packages.

## Resources
Use `references/creation-contract.md` and `../marketplace/references/catalog-contract.md` when selecting a source. Use `references/contract.md` and `assets/request.json` to construct a `/create-marketplace` request. Run `scripts/validate.py` for the bundled creation fixture.
