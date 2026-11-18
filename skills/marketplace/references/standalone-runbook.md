# Standalone marketplace runbook

Run from a Marketplace Agent package root. Python 3.10+ is needed for local scripts; source checks use Git, and private trails require POSIX owner-only permissions. The original four-catalog blueprint retains its `pmcro-marketplace/Everything-as-Agent` source locator. Local scaffolding writes in the selected workspace; it does not write to that GitHub repository or contact any provider.

```sh
python3 -B skills/creator/scripts/setup_marketplaces.py --target /absolute/workspace
python3 -B skills/creator/scripts/setup_marketplaces.py --target /absolute/workspace --apply
python3 -B skills/marketplace/scripts/validate_catalogs.py --catalog-root /absolute/workspace
python3 -B skills/marketplace/scripts/resolve.py discover --catalog-root /absolute/workspace
```

Supply `--checkout OWNER/REPO=/absolute/checkout` to check the matching GitHub origin and pinned commit. Supply `--host PLUGIN=SKILL,SKILL` only for freshly observed host inventory. Membership and source resolution are not installation, invocation, or authorization. The existing catalog membership methods still require their authorized provider; the local CLI does not publish or add/remove plugins.

## Read-only provider dispatch

Use a trusted local checkout of `shawn2024bellazan-prog/agent-skills` containing the reviewed pin. Do not pass an arbitrary binary or runtime handler. DotAgents `doctor` and `list` use the trusted Sentry DotAgents 3.4.0 CLI on `PATH` against an initialized project.

```sh
printf '%s' '{"operation":"list"}' |
  python3 -B skills/marketplace/scripts/resolve.py resolve \
    --catalog-root /absolute/workspace --marketplace project-management \
    --agent dotagents-agent --plugin dotagents --skill list \
    --checkout shawn2024bellazan-prog/agent-skills=/absolute/agent-skills \
    --project /absolute/project --project-id example
```

The command above is a preflight. For an independently authorized execution add `--execute --allow /dotagents:list`. The `doctor` variant uses `--skill doctor`, `{"operation":"check"}`, and `/dotagents:doctor`. Project lifecycle calls use `--agent project-agent --plugin projects --skill project-lifecycle`, `{"operation":"status"}` or `{"operation":"runtime"}`, and `--pmcro-root /absolute/private/.pmcro`; the exact execution grant is `/projects:project-lifecycle`. Runtime resolution requires Project Agent to have initialized the workspace with its private-state exclusions first. A bound runtime additionally requires the independently reviewed `--bound-adapter /absolute/file` and will not start a runtime or create a host project.

Execution requires explicit `--project-id` and a pre-existing private `~/.pmcro/projects/<id>/` scope; the resolver never creates a registry entry. If the durable start cannot be written, no provider is invoked. `UNVERIFIED` means inspect the private trail before retrying. The receipts are local; do not post the full receipt or the raw frames. Creator routes stay blocked unless their own real provider is configured and authorized.

## Catalog-only acceptance

For an already registered local proof scope:

```sh
python3 -B skills/marketplace/scripts/catalog_cycle.py run --project-id example
python3 -B skills/marketplace/scripts/catalog_cycle.py verify --project-id example --trail-id UUID
```

The wrapper produces seven correlated PMCR-O phases and three actual local catalog function frames. Reopening checks frame digests, phase correlation, and membership/route evidence. The wrapper is optional; the individual skill commands do not require this wrapper or an `eng/` folder. GitHub Actions uses the same wrapper with a disposable private home and exposes only a redacted result and correlation ID, not raw frames or independent approval.
