---
name: creator
description: Marketplace creation subagent that creates a new marketplace catalog/container after discovery proves a genuine gap.
---
# creator

## Purpose
Own `/create-marketplace`: create the marketplace catalog and selected source/container without creating the plugin packages that will later be added to it.

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
See `references/contract.md`, `references/creation-contract.md`, `../marketplace/references/catalog-contract.md`, and `assets/request.json`.


## Script reference

Scripts are not loaded into context. An agent runs one only when a step needs it, and you can run the same command by hand from this skill's folder.

| Script | Purpose | Manual run |
|---|---|---|
| `scripts/validate.py` | Structural self-check: verifies the skill's required files (and request.json contents where applicable). Takes no arguments; prints `PASS: <skill>` and exits 0, or prints `FAIL: ...` and exits 1. | `python scripts/validate.py` |
