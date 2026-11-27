# Creation Contract

Input:
- marketplace name
- source type
- source locator inputs
- visibility/authorization when required
- initial metadata

Procedure:
1. Discover.
2. Deny duplicates.
3. Create or verify the source/container.
4. Initialize `marketplace.yaml`.
5. Validate the marketplace catalog.
6. Return evidence.

For `github-repository`, repository creation is delegated to GitHub Agent. Marketplace Agent resumes after GitHub returns repository evidence.
