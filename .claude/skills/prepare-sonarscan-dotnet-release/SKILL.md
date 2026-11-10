---
name: prepare-sonarscan-dotnet-release
description: Prepare and verify beta or stable releases of highbyte/sonarscan-dotnet using its bundled sample, local Docker verification, and GitHub branch/tag verification workflow.
---

# Prepare and verify a SonarScanner release

This is an optional preparation and verification guide. The owner can publish through GitHub.com's **Create release** page. Agent-driven publication requires explicit authorization; invoking this skill alone does not authorize it.

Locate the scanner checkout from task context, verify its remote, and read `BUILD_RELEASE.md` and `samples/README.md`. Ask for the location if unavailable. Follow applicable repository/user authorization and credential rules; this skill grants no permission to publish, commit/push, change secrets, merge, or delete resources.

1. Establish beta/stable, version, source commit/branch, image tag/digest, daemon/architecture, and sample SonarCloud configuration. Preserve local changes and workspace preferences. Reuse verified stages only when the candidate's image source and digest match.
2. For a stable .NET upgrade, require the final SDK and update the sample framework. Keep preview/RC descriptions for preview SDKs; preserve historical compatibility entries and published tags.
3. Update action/image versions and current examples. Build AMD64 using the guide's Colima/Rosetta path on Apple Silicon. Run `samples/verify-image.sh --build-only`, then its authenticated scan with scoped credentials. Require fresh tests/coverage and the exact analysis's gate; resolve relevant failures before publishing.
4. When separately authorized, publish the image and source branch, then use `verify-sample.yml` to test the action commit/branch. Stable normally follows an approved merge into the discovered default branch and successful checks; retest if merging changes the image source.
5. Hand off the tested commit, image digest, and verification results for the owner to create the Git tag and GitHub release through GitHub.com's **Create release** page, following `BUILD_RELEASE.md`. Create a tag or release yourself only when explicitly asked to perform agent-driven publication; use the tested target and correct prerelease flag.
6. After publication, for both beta and stable, dispatch the same workflow with `action_ref` set to the published tag. Verify the selected ref/image, tests, coverage, processing, and gate. A skipped workflow or an uploaded report alone is not completed verification.

Stop at missing authorization, credentials, or configuration; report the specific blocker. Local credentials do not update GitHub secrets. Fix and rerun affected checks within scope; obtain a decision before proceeding with unresolved gate findings. Report source commit, action/image tag and digest/architecture, run URLs, results, and skipped stages. Do not merge or clean up resources automatically.
