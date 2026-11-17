# Contract

Agent: `@marketplace-agent`  
Plugin: `marketplace`  
Skill/Subagent: `marketplace`

Functions:

- `discover` -> `/marketplace:marketplace:discover`
- `register` -> `/marketplace:marketplace:register`
- `install` -> `/marketplace:marketplace:install`
- `enable` -> `/marketplace:marketplace:enable`
- `validate` -> `/marketplace:marketplace:validate`
- `sync` -> `/marketplace:marketplace:sync`
- `publish` -> `/marketplace:marketplace:publish`

Status vocabulary: `PASS`, `FAIL`, `LOOP`, `HALT`, `BLOCKED`, `NOT_INVOKED`.

Invariant: emission, installation, enablement, and execution are distinct states.
