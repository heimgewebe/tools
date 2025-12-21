import requests
import time
import sys
import os

BASE_URL = "http://127.0.0.1:9999"

def wait_for_server():
    for _ in range(10):
        try:
            requests.get(f"{BASE_URL}/api/health")
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

def run_tests():
    if not wait_for_server():
        print("Server did not start")
        sys.exit(1)

    print("Checking health...")
    r = requests.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200
    print(r.json())

    print("Checking repos...")
    r = requests.get(f"{BASE_URL}/api/repos")
    assert r.status_code == 200
    repos = r.json()
    print("Repos:", repos)

    print("Creating job for 'tests' repo...")
    # 'tests' folder exists in merger/repoLens
    payload = {
        "repos": ["tests"],
        "level": "max",
        "plan_only": True,
        "json_sidecar": True
    }
    r = requests.post(f"{BASE_URL}/api/jobs", json=payload)
    assert r.status_code == 200
    job = r.json()
    job_id = job["id"]
    print(f"Job created: {job_id}")

    print("Polling job...")
    for _ in range(20):
        r = requests.get(f"{BASE_URL}/api/jobs/{job_id}")
        assert r.status_code == 200
        job = r.json()
        status = job["status"]
        print(f"Status: {status}")
        if status in ["succeeded", "failed"]:
            break
        time.sleep(1)

    if job["status"] != "succeeded":
        print("Job failed or timed out")
        print(job)
        sys.exit(1)

    print("Checking artifacts...")
    r = requests.get(f"{BASE_URL}/api/artifacts")
    assert r.status_code == 200
    artifacts = r.json()
    assert len(artifacts) > 0
    art = artifacts[0]
    print(f"Artifact found: {art['id']}")

    # Download artifact
    print("Downloading MD artifact...")
    r = requests.get(f"{BASE_URL}/api/artifacts/{art['id']}/download?key=md")
    assert r.status_code == 200
    print("MD content length:", len(r.content))

    print("Tests passed!")

if __name__ == "__main__":
    run_tests()
