# Marketplace Subagent Contract

Agent: `@marketplace-agent`  
Plugin: `marketplace`  
Skill/Subagent: `marketplace`

Functions:

- `discover` -> `/marketplace:marketplace:discover`
- `add-source` -> `/marketplace:marketplace:add-source`
- `add-plugin` -> `/marketplace:marketplace:add-plugin`
- `remove-plugin` -> `/marketplace:marketplace:remove-plugin`
- `list-plugins` -> `/marketplace:marketplace:list-plugins`
- `validate` -> `/marketplace:marketplace:validate`
- `sync` -> `/marketplace:marketplace:sync`
- `publish` -> `/marketplace:marketplace:publish`

Status vocabulary: `PASS`, `FAIL`, `LOOP`, `HALT`, `BLOCKED`, `NOT_INVOKED`.

Invariant: source existence, catalog validity, plugin membership, installation, enablement, and runtime execution are distinct states.

## add-plugin input contract

```yaml
marketplace_ref: <marketplace identity>
plugin_ref: <existing plugin identity or resolvable package reference>
enabled: true
```

`plugin_ref` MUST resolve to an already-created plugin package. If it does not exist, return `BLOCKED` or route creation to Plugin Agent before retrying membership.
