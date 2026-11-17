# Contract

Agent: `@marketplace-agent`  
Plugin: `marketplace`  
Skill/Subagent: `creator`

Function:

- `create` -> `/marketplace:creator:create`

Creation requires prior discovery evidence proving the target marketplace is genuinely missing.

Status vocabulary: `PASS`, `FAIL`, `LOOP`, `HALT`, `BLOCKED`, `NOT_INVOKED`.

Invariant: a proposed artifact or emitted invocation is not proof of creation.
