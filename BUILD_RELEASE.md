# Building new release

_TODO: This workflow should be improved_

- Clone the GitHub repository locally.
- Create new Git branch (feature/name-of-feature).
- Decide what the new full version number should be. If it's a pre-release, use -beta suffix in version number.
- Build and push docker image
  - Authenticate to ghcr.io using [these instructions](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-to-the-container-registry)
  - `docker build -t ghcr.io/highbyte/sonarscan-dotnet:v1.0.0 .` where v1.0.0 is the full version number.
  - `docker push ghcr.io/highbyte/sonarscan-dotnet:v1.0.0` where v1.0.0 is the full version number.
- Update `action.yml` to point to the new docker tag version.
- Update `README.md` instructions to the new version.
- Push new branch from local repository to GitHub.
- Create [GitHub release](https://github.com/highbyte/sonarscan-dotnet/releases) with the full version number.
  - If pre-rerelease (beta), check the Pre-release box.
  - Check the box to release it to the GitHub Marketplace.
  - Publish the release.
- Verify the release from a workflow in another repo using the new version.
- If the version is not a pre-release, create a GitHub PR to merge the new branch to master.
