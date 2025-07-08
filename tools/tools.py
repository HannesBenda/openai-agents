import os
import subprocess
import requests
import json

def fetch_test_case(api_url: str) -> dict:
    """
    Fetches a test case from the given URL.
    The response is expected to be a JSON object containing 'Problem_statement', 'git_clone', 'FAIL_TO_PASS', 'PASS_TO_PASS', and 'instance_id'.
    Args:
        api_url (str): The URL to fetch the test case from.
    Returns:
        dict: The parsed JSON test case.
    """
    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"Invalid response: {response.status_code}")
    testcase = response.json()
    return testcase

def clone_repo(git_clone: str, local_repo: str):
    """
    Clones a Git repository from the given URL to a local path.
    Args:
        git_clone (str): The URL of the Git repository.
        local_repo (str): The local directory to clone the repository into.
    Returns:
        str: A success message or an error message.
    """
    parts = git_clone.split("&&")
    clone_part = parts[0].strip()
    checkout_part = parts[-1].strip() if len(parts) > 1 else None

    repo_url = clone_part.split()[2]

    print(f"Cloning repository {repo_url} into {local_repo}...")
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    subprocess.run(["git", "clone", repo_url, local_repo], check=True, env=env)
    
    if checkout_part:
        commit_hash = checkout_part.split()[-1]
        print(f"Checking out commit: {commit_hash}")
        subprocess.run(["git", "checkout", commit_hash], cwd=local_repo, check=True)

def verify_solution(test_payload: dict) -> dict:
    res = requests.post("http://localhost:8082/test", json=test_payload)
    res.raise_for_status()
    # print(f"----Response: {res.json()}")
    result_raw = res.json().get("harnessOutput", "{}")
    result_json = json.loads(result_raw)
    if not result_json:
        raise ValueError("No data in harnessOutput - possible evaluation error or emtpy change file")
    return result_json


def log_results(result_json: dict, start_dir: str, LOG_FILE: str, index: int, token_total):
    instance_id = next(iter(result_json))
    tests_status = result_json[instance_id]["tests_status"]
    fail_pass_results = tests_status["FAIL_TO_PASS"]
    fail_pass_total = len(fail_pass_results["success"]) + len(fail_pass_results["failure"])
    fail_pass_passed = len(fail_pass_results["success"])
    pass_pass_results = tests_status["PASS_TO_PASS"]
    pass_pass_total = len(pass_pass_results["success"]) + len(pass_pass_results["failure"])
    pass_pass_passed = len(pass_pass_results["success"])

    os.chdir(start_dir)
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n--- TESTCASE {index} ---\n")
        log.write(f"FAIL_TO_PASS passed: {fail_pass_passed}/{fail_pass_total}\n")
        log.write(f"PASS_TO_PASS passed: {pass_pass_passed}/{pass_pass_total}\n")
        log.write(f"Total Tokens used: {token_total}")
    print(f"Test case {index} completed and logged")
