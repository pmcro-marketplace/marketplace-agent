# Invocation Contract

Human surface:

```text
@marketplace-agent /<function> [arguments]
```

Canonical ownership:

```text
Agent:  @marketplace-agent
Plugin: marketplace
```

## Function resolution

```text
@marketplace-agent /create-marketplace
  -> /marketplace:creator:create-marketplace

@marketplace-agent /setup
  -> /marketplace:creator:setup

@marketplace-agent /discover
  -> /marketplace:marketplace:discover

@marketplace-agent /resolve
  -> /marketplace:marketplace:resolve

@marketplace-agent /add-source
  -> /marketplace:marketplace:add-source

@marketplace-agent /add-plugin
  -> /marketplace:marketplace:add-plugin

@marketplace-agent /remove-plugin
  -> /marketplace:marketplace:remove-plugin

@marketplace-agent /list-plugins
  -> /marketplace:marketplace:list-plugins

@marketplace-agent /validate
  -> /marketplace:marketplace:validate

@marketplace-agent /sync
  -> /marketplace:marketplace:sync

@marketplace-agent /publish
  -> /marketplace:marketplace:publish
```

## Delegation law

Marketplace Agent owns the marketplace catalog.

It delegates:
- plugin package creation/update -> `@plugin-agent`
- GitHub repository creation/read/write -> `@github-agent`
- lifecycle interception -> `@hook-agent`, only when a real lifecycle provider exists

For `source.type = github-repository`, `/create-marketplace` may delegate repository creation to GitHub Agent, then Marketplace Agent writes and validates the marketplace catalog in that repository.

## Execution law

```text
RESOLVE
-> EMIT exact function
-> invoke applicable Hook function only when actually executable
-> INVOKE real target provider/capability
-> VERIFY resulting marketplace state
-> RETURN EVIDENCE
```

Emission is not invocation.
A GitHub repository existing does not by itself prove a valid marketplace catalog.
A plugin package existing does not by itself prove marketplace membership.
