#!/usr/bin/env python3
"""Build/test the sample in a Docker image, optionally verifying a SonarCloud scan."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

from check_analysis import check_analysis


SAMPLE_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY = SAMPLE_DIRECTORY.parent


def command_output(command):
    return subprocess.check_output(command, cwd=REPOSITORY, text=True).strip()


def run(args):
    if args.timeout <= 0:
        raise ValueError("The processing timeout must be positive.")
    token = os.environ.get("SONAR_TOKEN", "")
    if not args.build_only:
        for name, value in (("SONAR_TOKEN", token), ("project key", args.project_key),
                            ("organization", args.organization)):
            if not value:
                raise ValueError(name + " is required for a scan; use --build-only for token-free tests.")
        for name, value in (("project key", args.project_key), ("organization", args.organization),
                            ("branch", args.branch), ("project name", args.project_name)):
            if not re.fullmatch(r"[A-Za-z0-9_.:/ -]+", value):
                raise ValueError(name + " contains characters unsupported by the scanner entrypoint.")

    docker = ["docker"] + (["--context", args.context] if args.context else [])
    architecture = command_output(docker + ["image", "inspect", args.image,
                                           "--format", "{{.Os}}/{{.Architecture}}"])
    if architecture != args.platform:
        raise ValueError("Image architecture is " + architecture + "; expected " + args.platform + ".")
    print("Image:", args.image, architecture, flush=True)
    run_id = uuid.uuid4().hex
    results = ".artifacts/" + run_id
    env = dict(os.environ)
    command = docker + ["run", "--rm", "-i", "--platform", args.platform, "--log-driver", "none",
                        "--workdir", "/github/workspace", "--mount",
                        "type=bind,src=" + str(REPOSITORY) + ",dst=/github/workspace"]
    # Worktree metadata uses host paths, which are not valid inside Linux containers on Windows.
    common_git = Path(command_output(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"]))
    if common_git != REPOSITORY / ".git":
        git_directory = Path(command_output(["git", "rev-parse", "--absolute-git-dir"]))
        git_pointer = SAMPLE_DIRECTORY / results / "gitdir"
        git_pointer.parent.mkdir(parents=True, exist_ok=True)
        with git_pointer.open("w", encoding="utf-8", newline="\n") as pointer:
            pointer.write("gitdir: /git-metadata/" + git_directory.relative_to(common_git).as_posix() + "\n")
        command += ["--mount", "type=bind,src=" + str(common_git) + ",dst=/git-metadata,readonly",
                    "--mount", "type=bind,src=" + str(git_pointer) + ",dst=/github/workspace/.git,readonly"]

    if args.build_only:
        script = '''set -euo pipefail
dotnet restore samples/ScanSample.slnx --locked-mode
dotnet build samples/ScanSample.slnx --no-restore
dotnet test samples/ScanSample.slnx --no-build --logger trx --results-directory "samples/''' + results + '''" --collect:"XPlat Code Coverage" -- DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=opencover
'''
    else:
        scan_environment = {
            "INPUT_SONARPROJECTKEY": args.project_key,
            "INPUT_SONARPROJECTNAME": args.project_name,
            "INPUT_SONARORGANIZATION": args.organization,
            "INPUT_SONARHOSTNAME": "https://sonarcloud.io",
            "INPUT_DOTNETPREBUILDCMD": "dotnet restore samples/ScanSample.slnx --locked-mode",
            "INPUT_DOTNETBUILDARGUMENTS": "samples/ScanSample.slnx --no-restore",
            "INPUT_DOTNETTESTARGUMENTS": 'samples/ScanSample.slnx --no-build --logger trx --results-directory samples/' + results + ' --collect:"XPlat Code Coverage" -- DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=opencover',
            "INPUT_DOTNETDISABLETESTS": "false",
            # Local verification must include newly added sample files before they are committed.
            "INPUT_SONARBEGINARGUMENTS": '/d:sonar.scanner.scanAll=false /d:sonar.scm.exclusions.disabled=true /d:sonar.projectBaseDir=/github/workspace/samples /d:sonar.branch.name="' + args.branch + '" /d:sonar.cs.opencover.reportsPaths="samples/' + results + '/**/coverage.opencover.xml" /d:sonar.cs.vstest.reportsPaths="samples/' + results + '/*.trx"',
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF": "refs/heads/" + args.branch,
            "GITHUB_REPOSITORY": "highbyte/sonarscan-dotnet",
            "GITHUB_HEAD_REF": "",
            "GITHUB_BASE_REF": "",
        }
        env.update(scan_environment)
        for key in ["SONAR_TOKEN", *scan_environment]:
            command += ["--env", key]
        script = '''set -eo pipefail
set +x
echo() {
    local arg
    local -a redacted=()
    for arg in "$@"; do
        redacted+=("${arg//"$SONAR_TOKEN"/[REDACTED]}")
    done
    builtin echo "${redacted[@]}"
}
source /entrypoint.sh
'''
    command += ["--entrypoint", "bash", args.image, "-s"]
    process = subprocess.Popen(command, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True)
    try:
        # Keep Bash input as LF even when Python is running natively on Windows.
        process.stdin.reconfigure(newline="\n")
        process.stdin.write(script)
        process.stdin.close()
        for line in process.stdout:
            print(line.replace(token, "[REDACTED]") if token else line, end="", flush=True)
        if process.wait() != 0:
            raise RuntimeError("Docker build/test/scan failed.")
    except BaseException:
        if process.poll() is None:
            process.terminate()
            process.wait()
        raise

    reports = list((SAMPLE_DIRECTORY / results).glob("*.trx"))
    if not reports:
        raise RuntimeError("No fresh TRX report was generated.")
    for report in reports:
        counters = ET.parse(report).find(".//{*}Counters")
        if counters is None or int(counters.get("passed", "0")) == 0 or int(counters.get("failed", "0")) or int(counters.get("error", "0")):
            raise RuntimeError("The TRX report does not contain passing tests.")
    if not list((SAMPLE_DIRECTORY / results).glob("**/coverage.opencover.xml")):
        raise RuntimeError("No fresh OpenCover report was generated.")
    print("Fresh test and coverage reports verified.", flush=True)
    if not args.build_only:
        check_analysis(REPOSITORY / ".sonarqube/out/.sonar/report-task.txt", args.branch, token, args.timeout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="An image already built or pulled into the selected daemon")
    parser.add_argument("--context", help="Optional Docker context, e.g. colima-rosetta-build")
    parser.add_argument("--platform", choices=["linux/amd64", "linux/arm64"], default="linux/amd64")
    parser.add_argument("--build-only", action="store_true", help="Run build/tests/coverage without a token or upload")
    parser.add_argument("--project-key", default=os.environ.get("SONAR_PROJECT_KEY"))
    parser.add_argument("--organization", default=os.environ.get("SONAR_ORGANIZATION"))
    parser.add_argument("--project-name", default="SonarScanner .NET sample")
    parser.add_argument("--branch", default=command_output(["git", "branch", "--show-current"]) or "sample-verification")
    parser.add_argument("--timeout", type=int, default=300, help="SonarCloud processing timeout in seconds")
    args = parser.parse_args()
    try:
        run(args)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, KeyError) as error:
        token = os.environ.get("SONAR_TOKEN", "")
        message = str(error).replace(token, "[REDACTED]") if token else str(error)
        print("Verification failed:", message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
