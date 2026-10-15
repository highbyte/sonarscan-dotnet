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

## Set up AMD64 container execution

The release image targets `linux/amd64`, matching the GitHub-hosted Linux runner. Choose a supported execution setup for your host, then use the same build, verification, and publish commands below. Ubuntu ARM64/QEMU is described separately as an experimental build path, not a supported .NET verification environment. Run shell examples in a Bash-compatible terminal from the scanner checkout. Requirements: Docker CLI with Buildx, a running Linux Docker daemon, Git, and Python 3.

### Native AMD64 Linux or Windows with Docker Desktop

Use the existing Docker daemon; on Windows, select Linux containers. No CPU emulation is needed on an AMD64 host. For native PowerShell verification, see the [sample launcher instructions](samples/README.md#windows-powershell).

### Ubuntu ARM64 with Docker Engine

Use a native AMD64 Docker host or GitHub-hosted AMD64 runner for release verification. The local ARM64 Docker Engine can still build and test ARM64 images. Lima is not required.

QEMU can enable AMD64 container execution on the existing ARM64 engine, but [Microsoft does not support running .NET under QEMU](https://github.com/dotnet/core/blob/main/release-notes/11.0/supported-os.md#notes). The image build and `dotnet --info` may succeed while `dotnet restore` or tests crash. A successful emulated build is not release verification.

For an experimental AMD64 build attempt, register QEMU's AMD64 emulator with the Ubuntu host's `binfmt_misc` handlers, following [Docker's emulation setup](https://docs.docker.com/build/building/multi-platform/#install-qemu-manually):

```sh
docker run --privileged --rm tonistiigi/binfmt --install amd64
```

This privileged setup changes the Docker host's executable-format handlers; obtain approval before an agent runs it. It installs emulation support, not another Docker engine. Registration may need to be repeated after the host reboots unless the host restores it automatically. If Docker runs in an Ubuntu VM, the change applies to that VM.

QEMU can be slower than native execution. If the sample verifier fails silently after printing the image architecture, try `dotnet restore` directly to reveal runtime crashes. An `AccessViolationException` or `qemu_MSBuild_*.core` dump indicates a runtime crash, not a failing sample assertion. Use native AMD64 execution for verification; the macOS Rosetta setup below is another option when an Apple Silicon machine is available.

### macOS with Apple Silicon

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
```

The VM remains ARM64; Rosetta translates AMD64 commands. The context override applies only to this terminal and preserves the default context. Keep it set for every shared command below so login, build, verification, and push use the same daemon. The sample verifier inherits `DOCKER_CONTEXT`; no extra `--context` argument is needed.

When finished with the release workflow, optionally stop this profile and clear the override:

```sh
colima stop --profile rosetta-build
unset DOCKER_CONTEXT
```

Images and cache remain available for subsequent builds.

### Check AMD64 execution on the selected daemon

After host setup, run:

```sh
docker run --rm --platform linux/amd64 alpine uname -m
```

Expected output: `x86_64`. An `exec format error` means AMD64 execution is unavailable on the selected daemon; fix host setup before building the release image.

## Authenticate and build

The following commands are shared by the supported host setups. They can also be used for an experimental QEMU build, subject to the limitation above. Use the same daemon and Docker CLI configuration for login, build, verification, and push.

Create a [GitHub personal access token (classic)](https://github.com/settings/tokens/new?scopes=write:packages) with `write:packages`, following [GHCR authentication instructions](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-to-the-container-registry). Then run:

```sh
docker login ghcr.io --username highbyte
```

Paste the token at the hidden `Password:` prompt. Automated login should use `--password-stdin`; do not put credentials in arguments or committed files.

```sh
docker build --platform linux/amd64 -t "$IMAGE" .
docker image inspect "$IMAGE" --format '{{.Os}}/{{.Architecture}}'
samples/verify-image.sh --image "$IMAGE" --build-only
```

The inspection must report `linux/amd64`. The verifier checks that architecture, builds the sample, runs its tests, and checks fresh coverage reports. `--build-only` needs no SonarCloud credential and performs no analysis upload. Then perform the [authenticated sample scan](samples/README.md#sonarcloud-setup) against the separate sample project. Require successful analysis processing, coverage import, and quality gate before proceeding. Resolve relevant warnings/advisories; report unresolved findings explicitly.

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

Push the branch containing the workflow once to register it with GitHub before the first CLI dispatch. Watch the run for the intended commit/ref, confirm the image/digest and tests, and wait for the gate. The existing action itself does not wait for SonarCloud; the sample verification workflow does.

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

## Optional agent skill

[release-sonarscan-dotnet](.agents/skills/release-sonarscan-dotnet/SKILL.md) guides the release stages using this document and the sample scripts. The repository includes regular files in both discovery locations, so no installation or symlink support is needed when working in this checkout:

| Agent | Repository skill | Invocation |
| --- | --- | --- |
| Codex | [`.agents/skills/release-sonarscan-dotnet/SKILL.md`](.agents/skills/release-sonarscan-dotnet/SKILL.md) | `$release-sonarscan-dotnet` |
| Claude Code | [`.claude/skills/release-sonarscan-dotnet/SKILL.md`](.claude/skills/release-sonarscan-dotnet/SKILL.md) | `/release-sonarscan-dotnet` |

Include beta or stable and the intended version in the request. Detailed procedures and scripts remain shared in this repository.

Edit `.agents/skills/release-sonarscan-dotnet/SKILL.md`, then copy the instructions to the Claude Code location:

```sh
cp .agents/skills/release-sonarscan-dotnet/SKILL.md .claude/skills/release-sonarscan-dotnet/SKILL.md
```

Codex metadata stays in `.agents/skills/release-sonarscan-dotnet/agents/openai.yaml`; it does not need a Claude Code copy. The Docker build workflow checks that the two `SKILL.md` files match before building the image. Synchronization is manual; CI fails if the copies differ.

For use outside this checkout, install the matching repository skill folder in the agent's user skills directory (`~/.agents/skills/` for Codex or `~/.claude/skills/` for Claude Code), inspecting an existing installation before replacing it. Other agents supporting `SKILL.md` can install the instructions in their own skill location.
