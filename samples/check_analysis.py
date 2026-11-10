#!/usr/bin/env python3
"""Wait for an exact SonarCloud analysis and require its quality gate and coverage."""
import argparse
import base64
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def check_analysis(task_file, branch, token, timeout=300):
    if timeout <= 0:
        raise ValueError("The processing timeout must be positive.")
    properties = dict(line.split("=", 1) for line in Path(task_file).read_text().splitlines() if "=" in line)
    task_id = properties["ceTaskId"]
    credential = base64.b64encode((token + ":").encode()).decode()

    def get(path, **params):
        url = "https://sonarcloud.io/api/" + path + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={"Authorization": "Basic " + credential})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    deadline = time.monotonic() + timeout
    previous_status = None
    while True:
        task = get("ce/task", id=task_id)["task"]
        status = task["status"]
        if status != previous_status:
            print("SonarCloud processing:", status, flush=True)
            previous_status = status
        if status not in ("PENDING", "IN_PROGRESS"):
            break
        if time.monotonic() >= deadline:
            raise RuntimeError("Timed out waiting for SonarCloud processing.")
        time.sleep(5)
    if status != "SUCCESS":
        raise RuntimeError("SonarCloud did not complete the analysis successfully.")

    gate = get("qualitygates/project_status", analysisId=task["analysisId"])["projectStatus"]
    print("Quality gate:", gate["status"], flush=True)
    for condition in gate["conditions"]:
        if condition["status"] == "ERROR":
            print(condition["metricKey"], "actual:", condition.get("actualValue"),
                  "threshold:", condition["errorThreshold"], flush=True)
    component = get("measures/component", component=task["componentKey"], branch=branch,
                    metricKeys="coverage")["component"]
    coverage = next((measure["value"] for measure in component["measures"]
                     if measure["metric"] == "coverage"), None)
    if coverage is None:
        raise RuntimeError("The sample analysis has no coverage measure; verify report import.")
    print("SonarCloud coverage:", coverage + "%", flush=True)
    if float(coverage) < 100:
        raise RuntimeError("The sample requires 100% coverage; verify tests and report import.")
    if gate["status"] != "OK":
        raise RuntimeError("The SonarCloud quality gate failed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    token = os.environ.get("SONAR_TOKEN")
    if not token:
        parser.error("SONAR_TOKEN must be supplied in the environment.")
    try:
        check_analysis(args.task_file, args.branch, token, args.timeout)
    except (OSError, KeyError, ValueError, RuntimeError, urllib.error.URLError) as error:
        print("Analysis verification failed:", str(error).replace(token, "[REDACTED]"), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
