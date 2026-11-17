# Invocation Contract

Human surface:

`@marketplace-agent /<function> [arguments]`

Canonical ownership:

```text
Agent: @marketplace-agent
Plugin: marketplace
Skill/Subagent: marketplace | creator
Function: concrete operation
```

Concrete functions:

```text
@marketplace-agent /discover  -> /marketplace:marketplace:discover
@marketplace-agent /create    -> /marketplace:creator:create
@marketplace-agent /register  -> /marketplace:marketplace:register
@marketplace-agent /install   -> /marketplace:marketplace:install
@marketplace-agent /enable    -> /marketplace:marketplace:enable
@marketplace-agent /validate  -> /marketplace:marketplace:validate
@marketplace-agent /sync      -> /marketplace:marketplace:sync
@marketplace-agent /publish   -> /marketplace:marketplace:publish
```

Hook Agent is the autonomous lifecycle layer above this plugin when installed and backed by a real runtime adapter.

Core flow:

`RESOLVE -> EMIT -> HOOK WHEN ACTUALLY EXECUTABLE -> INVOKE TARGET -> VERIFY -> EVIDENCE`

Marketplace installation, routing, or emitted function names do not prove runtime execution.

If a lifecycle provider is unavailable, the hook action is `NOT_INVOKED`.
If the target provider is unavailable or authorization blocks it, return `BLOCKED` or `NOT_INVOKED`.

**Emission is not invocation.**
