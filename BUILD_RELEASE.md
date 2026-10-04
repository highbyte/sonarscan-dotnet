# Building and verifying a release

A release has two artifacts: the GHCR Docker image and the GitHub action tag. The tagged `action.yml` must reference the matching image. Use the [sample and verification scripts](samples/README.md) for local and GitHub tests. Follow applicable approval rules before commits, pushes, credential changes, merges, or publishing.

## Choose beta or stable

| Release | Preparation | GitHub release |
| --- | --- | --- |
| Beta | Use a preview/RC SDK for a new .NET version, or a final SDK for a dependency candidate. Choose a unique version such as `v2.6.0-beta2`. | Target the tested feature branch/commit; select **Set as a pre-release**. |
| Stable .NET upgrade | Wait for the final SDK, update the Dockerfile and sample target framework, rebuild, and repeat verification. Retagging an RC image does not upgrade its SDK. | Normally merge approved, tested changes into the configured default branch first; leave **Set as a pre-release** unchecked. |
| Stable dependency update | Keep a final SDK, bump dependencies, and choose the appropriate next version. | Follow the same stable verification path. |

Do not overwrite published image or Git tags. Discover the default branch:

```sh
gh repo view highbyte/sonarscan-dotnet --json defaultBranchRef --jq '.defaultBranchRef.name'
```

From the scanner checkout, set the candidate version and branch:

```sh
RELEASE_VERSION=v2.6.0-beta2
SCANNER_BRANCH=feature/net11-dependencies
IMAGE="ghcr.io/highbyte/sonarscan-dotnet:$RELEASE_VERSION"
```

Update the Dockerfile, sample framework/dependencies and lock files, `action.yml` image tag, and current README/sample usage examples as needed. Preserve historical compatibility entries. Keep preview/RC support explicit when applicable.

## Authenticate and build

For Apple Silicon, complete the [Colima setup](#macos-with-apple-silicon) below first. Use the same daemon and Docker CLI configuration for login, build, verification, and push.

Create a [GitHub personal access token (classic)](https://github.com/settings/tokens/new?scopes=write:packages) with `write:packages`, following [GHCR authentication instructions](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-to-the-container-registry). Then run:

```sh
docker login ghcr.io --username highbyte
```

Paste the token at the hidden `Password:` prompt. Automated login should use `--password-stdin`; do not put credentials in arguments or committed files.

```sh
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker build -t "$IMAGE" .
samples/verify-image.sh --image "$IMAGE" --build-only
```

This validates the image's AMD64 architecture, sample build/tests, and fresh coverage. Then perform the [authenticated sample scan](samples/README.md#sonarcloud-setup) against the separate sample project. Require successful analysis processing, coverage import, and quality gate before proceeding. Resolve relevant warnings/advisories; report unresolved findings explicitly.

## Publish the image and test the action branch

After verification and authorization to publish:

```sh
docker push "$IMAGE"
docker pull --platform linux/amd64 "$IMAGE"
```

Record the digest and ensure the GitHub runner can pull the package. Commit and push the candidate changes when authorized. The remote branch's `action.yml` must reference this image.

The automatic sample scan verifies the pushed action commit once SonarCloud settings are configured. For an explicit branch test, dispatch the sample workflow as described in [GitHub action verification](samples/README.md#github-action-verification):

```sh
gh workflow run verify-sample.yml --repo highbyte/sonarscan-dotnet \
  --ref "$SCANNER_BRANCH" -f "action_ref=$SCANNER_BRANCH"
```

The workflow must be available on the default branch before manual dispatch. Watch the run for the intended commit/ref, confirm the image/digest and tests, and wait for the gate. The existing action itself does not wait for SonarCloud; the sample verification workflow does.

## Publish the action release

For stable, complete the approved merge and required gates. If merging changes the image source, rebuild and repeat verification. On [Create Release](https://github.com/highbyte/sonarscan-dotnet/releases/new):

1. Create the tag matching `$RELEASE_VERSION`.
2. Set **Target** to the tested branch/commit; the default selection may still contain the older action.
3. Add current release notes and identify preview/RC versus final SDK support.
4. Select **Set as a pre-release** for beta; leave it unchecked for stable.
5. Select **Publish this Action to GitHub Marketplace** if offered and follow its eligibility requirements.
6. Publish the release.

Read back the release and its image reference:

```sh
gh release view "$RELEASE_VERSION" --repo highbyte/sonarscan-dotnet \
  --json tagName,isPrerelease,targetCommitish,url
gh api "repos/highbyte/sonarscan-dotnet/contents/action.yml?ref=$RELEASE_VERSION" \
  --jq '.content' | base64 --decode
```

## Verify the published release

For **both beta and stable**, run the same sample against the exact action release tag:

```sh
gh workflow run verify-sample.yml --repo highbyte/sonarscan-dotnet \
  --ref "$SCANNER_BRANCH" -f "action_ref=$RELEASE_VERSION"
gh run list --repo highbyte/sonarscan-dotnet --workflow verify-sample.yml --limit 5
```

Watch the new run with `gh run watch RUN_ID --repo highbyte/sonarscan-dotnet --exit-status`. Verify tag resolution, image digest, build/tests, imported coverage, server processing, and quality gate. A branch test alone does not verify the release tag. Report the commit, tag/digest/architecture, run URL, and results; do not automatically merge or clean up branches/worktrees.

## macOS with Apple Silicon

Use a separate Colima/Rosetta profile for AMD64 builds. Requirements: macOS 13+, Colima, and Docker CLI with Buildx. Rosetta avoids the .NET 11 RC1 crash seen under QEMU during scanner installation.

Install Rosetta once if needed:

```sh
softwareupdate --install-rosetta
```

In a separate terminal:

```sh
colima start --profile rosetta-build \
  --vm-type vz --arch aarch64 --vz-rosetta \
  --activate=false --ssh-config=false \
  --cpu 4 --memory 4 --disk 20
export DOCKER_CONTEXT=colima-rosetta-build
export DOCKER_DEFAULT_PLATFORM=linux/amd64
```

The VM remains ARM64; Rosetta translates AMD64 commands. The exports apply only to this terminal and preserve the default context. Run the commands above unchanged. You can also select this daemon using `docker --context colima-rosetta-build ...` or the sample script's `--context` option.

When finished, optionally stop this profile and clear the overrides:

```sh
colima stop --profile rosetta-build
unset DOCKER_CONTEXT DOCKER_DEFAULT_PLATFORM
```

Images and cache remain available for subsequent builds.

## Optional agent skill

[release-sonarscan-dotnet](skills/release-sonarscan-dotnet/SKILL.md) guides the release stages using this document and the sample scripts. To install in Codex, copy the folder to the local skills directory (inspect an existing installation before replacing it):

```sh
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/release-sonarscan-dotnet "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Invoke `$release-sonarscan-dotnet` with beta or stable and the intended version. Other agents supporting `SKILL.md` can install the same source folder in their own skill location.
