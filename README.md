# Marketplace Agent

Canonical repository: `pmcro-marketplace/marketplace-agent`.

Canonical identity:

```text
Agent:  @marketplace-agent
Plugin: marketplace
```

Skills are subagents; functions are concrete operations.

```text
marketplace
├── skill/subagent: marketplace
│   ├── discover
│   ├── register
│   ├── install
│   ├── enable
│   ├── validate
│   ├── sync
│   └── publish
└── skill/subagent: creator
    └── create
```

Human calls:

```text
@marketplace-agent /discover
@marketplace-agent /create
@marketplace-agent /register
@marketplace-agent /install
@marketplace-agent /enable
@marketplace-agent /validate
@marketplace-agent /sync
@marketplace-agent /publish
```

The installed Hook Agent may surround applicable executions, but it does not replace Marketplace Agent business functionality.

See `INVOCATION.md` for the exact internal capability identities.
