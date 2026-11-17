# Marketplace Source Types

## github-repository
A GitHub repository is the source/container. GitHub Agent owns repository operations. Marketplace Agent owns the marketplace catalog stored there.

Required source fields:
- `type: github-repository`
- `repository: owner/name`

## local-repository
A local filesystem or Git repository is the source/container.

Required source fields:
- `type: local-repository`
- `path`

## remote-repository
A non-GitHub remote repository or supported remote source is the source/container.

Required source fields:
- `type: remote-repository`
- `url`

Source creation is not marketplace validation. The catalog must also satisfy the catalog contract.
