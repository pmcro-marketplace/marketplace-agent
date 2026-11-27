# Marketplace Catalog Contract

Canonical authored manifest: `marketplace.yaml`.

Minimum conceptual fields:

```yaml
kind: Marketplace
version: 1
name: example-marketplace
source:
  type: github-repository
  repository: owner/example-marketplace
plugins: []
```

Each plugin entry MUST identify an existing plugin package rather than embed or recreate it. Marketplace Agent records membership; Plugin Agent owns package creation.

Example conceptual membership:

```yaml
plugins:
  - name: hook
    agent: hook-agent
    source: plugins_...
    enabled: true
```

Validation rules:
1. Marketplace identity is non-empty.
2. Source type is supported.
3. Source locator matches its type.
4. Plugin entries are unique by canonical plugin identity.
5. A plugin membership entry must point to an existing plugin identity or resolvable package.
6. Generated projections are not authoritative when an authored marketplace manifest exists.
