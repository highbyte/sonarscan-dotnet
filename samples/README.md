# Scanner verification sample

`ScanSample.slnx` contains a small temperature-conversion library and five tests covering successful conversions, the absolute-zero boundary, and invalid input. The target framework in `Directory.Build.props` follows the action's SDK. Package versions and lock files are pinned, and high/critical transitive NuGet advisories fail restore.

Run commands from the repository root. Requirements: Docker, Git, Python 3, and an image already built or pulled into the selected Docker daemon. GitHub verification uses Linux AMD64; on Apple Silicon use the Colima/Rosetta setup in [BUILD_RELEASE.md](../BUILD_RELEASE.md#macos-with-apple-silicon).

## Local build, tests, and coverage

```sh
samples/verify-image.sh --image ghcr.io/highbyte/sonarscan-dotnet:v2.6.0-beta --build-only
```

For the separate macOS daemon, add `--context colima-rosetta-build`, or select it through `DOCKER_CONTEXT`. Use `--help` for other options. `--build-only` requires no credentials and performs no SonarCloud upload.

Each run writes fresh TRX and OpenCover reports into ignored `samples/.artifacts/`. The script verifies successful tests and coverage generation. Build outputs and scanner working files are also ignored; do not commit generated artifacts.

## Windows (PowerShell)

Use Windows PowerShell 5.1 or PowerShell 7 with Python 3, Git, and Docker Desktop configured for Linux containers. The launcher looks for `py -3`, then `python3`, then `python` on `PATH`. The .NET SDK runs inside the image; no host SDK or Git Bash is required.

From the repository root:

```powershell
docker pull --platform linux/amd64 ghcr.io/highbyte/sonarscan-dotnet:v2.6.0-beta
.\samples\verify-image.ps1 --image ghcr.io/highbyte/sonarscan-dotnet:v2.6.0-beta --build-only
```

The PowerShell launcher accepts the same options as the Bash launcher and returns the verifier's exit code. Use `--help` to list options. After configuring the SonarCloud project as described below and supplying `SONAR_TOKEN` in the process environment through your approved credential mechanism, run:

```powershell
.\samples\verify-image.ps1 --image ghcr.io/highbyte/sonarscan-dotnet:v2.6.0-beta `
  --project-key your-org_sonarscan-dotnet-sample --organization your-org `
  --branch sample-verification
```

## SonarCloud setup

Create a separate SonarCloud project for this sample, with a project key such as `your-org_sonarscan-dotnet-sample`. Use manual CI-based analysis and assign your organization's quality gate to the project. Analyze the project's main branch once before relying on comparisons against it. Keep this project separate from any analysis of the action's own implementation. Verification requires an `OK` gate; `NONE` indicates an unevaluated gate and fails verification.

Set these GitHub repository variables and secret to enable the scan workflow:

| Setting | Kind | Value |
| --- | --- | --- |
| `SONAR_SAMPLE_PROJECT_KEY` | Variable | The sample project's key |
| `SONAR_ORGANIZATION` | Variable | Its SonarCloud organization key |
| `SONAR_TOKEN` | Secret | A token authorized to analyze the sample project |

Local scanning requires `SONAR_TOKEN` in the process environment, plus the project/organization settings. Supply credentials through your approved mechanism; never place a token in arguments, logs, or version control. For a manual terminal run, the following prompt hides input and scopes the variable to a subshell:

```sh
(
set +x
printf 'SonarCloud token: ' >&2
IFS= read -r -s SONAR_TOKEN
printf '\n' >&2
export SONAR_TOKEN
samples/verify-image.sh --image ghcr.io/highbyte/sonarscan-dotnet:v2.6.0-beta \
  --project-key your-org_sonarscan-dotnet-sample --organization your-org \
  --branch sample-verification
)
```

Alternatively supply non-secret `SONAR_PROJECT_KEY` and `SONAR_ORGANIZATION` environment variables. Use the SonarCloud main branch's name for the initial scan. The default branch name is the current Git branch; `--branch` selects the analysis branch explicitly.

The script runs the image's real entrypoint, masks its token-bearing echoes, disables Docker log persistence, and redacts the streamed output. Local scans include untracked sample source files so changes can be verified before committing. It then waits for the exact uploaded analysis, requires 100% sample coverage and an `OK` quality gate, and exits nonzero on failure. GitHub repository secrets are independent of local credentials.

## GitHub action verification

[Docker Image build](../.github/workflows/docker-image.yml) builds the candidate image and runs this sample without SonarCloud, on pushes and PRs. [Verify scanner action](../.github/workflows/verify-sample.yml) uses the published image referenced by the selected action's `action.yml`, then waits for the SonarCloud gate. The latter skips automatic runs until the project variables are configured; a skipped run is not scan verification.

Pushes verify the action at the workflow commit and register the verification workflow with GitHub. After that initial push, dispatch it from the development branch with an explicit action ref:

```sh
# Candidate action branch; replace the branch if needed.
gh workflow run verify-sample.yml --repo highbyte/sonarscan-dotnet \
  --ref feature/net11-dependencies -f action_ref=feature/net11-dependencies

# Published beta; use the exact stable tag for stable-release verification.
gh workflow run verify-sample.yml --repo highbyte/sonarscan-dotnet \
  --ref feature/net11-dependencies -f action_ref=v2.6.0-beta

gh run list --repo highbyte/sonarscan-dotnet --workflow verify-sample.yml --limit 5
```

The workflow checks out the sample from the workflow ref and the selected action into a separate directory. This lets a published tag be tested without modifying that tag or changing a consumer repository. Confirm the selected ref, pulled image/digest, build/tests, coverage import, and gate verdict in the new run. The verification step fails even if the action uploaded successfully but the quality gate failed.

When upgrading packages, regenerate their lock files intentionally with `dotnet restore samples/ScanSample.slnx --force-evaluate` using the matching SDK, then rerun verification.
