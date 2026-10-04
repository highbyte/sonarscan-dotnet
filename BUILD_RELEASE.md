# Building new release

_TODO: This workflow should be improved_

- Clone the GitHub repository locally.
- Create new Git branch (feature/name-of-feature).
- Decide what the new full version number should be. If it's a pre-release, use -beta suffix in version number.
- Build and push docker image
  - On macOS with Apple Silicon, complete the [Colima setup](#macos-with-apple-silicon) below first, then run the following commands in the same terminal.
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

## macOS with Apple Silicon

Use a separate Colima profile with Rosetta to build Linux AMD64 images for GitHub's standard Linux runners. This requires macOS 13 or later, Colima, and the Docker CLI with Buildx available. Rosetta avoids the .NET 11 RC1 crash observed during SonarScanner installation under QEMU emulation.

Install Rosetta once, if needed:

```sh
softwareupdate --install-rosetta
```

In a separate terminal, start the build profile and select it for that terminal:

```sh
colima start --profile rosetta-build \
  --vm-type vz --arch aarch64 --vz-rosetta \
  --activate=false --ssh-config=false \
  --cpu 4 --memory 4 --disk 20

export DOCKER_CONTEXT=colima-rosetta-build
export DOCKER_DEFAULT_PLATFORM=linux/amd64
```

The VM itself runs ARM64 Linux; Rosetta translates the AMD64 commands during the build. `DOCKER_DEFAULT_PLATFORM` ensures the existing `docker build` command produces an AMD64 image. Run the authentication, build, and push commands above unchanged in this terminal. The exports apply only to this terminal, and `--activate=false` preserves the configured default Docker context.

When finished, stop the build profile and clear the terminal's overrides:

```sh
colima stop --profile rosetta-build
unset DOCKER_CONTEXT DOCKER_DEFAULT_PLATFORM
```

Images and build cache remain in this profile for the next build.
