import urllib.request
import urllib.error
import json
import time
import sys
import os

BASE_URL = "http://127.0.0.1:9999"

def request(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method=method)
    if data is not None:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')

    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            content = response.read()
            return status, content
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except urllib.error.URLError:
        raise

def wait_for_server():
    for _ in range(10):
        try:
            urllib.request.urlopen(f"{BASE_URL}/api/health")
            return True
        except (urllib.error.URLError, ConnectionRefusedError):
            time.sleep(1)
    return False

def run_tests():
    if not wait_for_server():
        print("Server did not start")
        sys.exit(1)

    print("Checking health...")
    status, content = request("GET", "/api/health")
    assert status == 200
    print(json.loads(content))

    print("Checking repos...")
    status, content = request("GET", "/api/repos")
    assert status == 200
    repos = json.loads(content)
    print("Repos:", repos)

    print("Creating job for 'tests' repo...")
    payload = {
        "repos": ["tests"],
        "level": "max",
        "plan_only": True,
        "json_sidecar": True
    }
    status, content = request("POST", "/api/jobs", payload)
    assert status == 200
    job = json.loads(content)
    job_id = job["id"]
    print(f"Job created: {job_id}")

    print("Polling job...")
    for _ in range(20):
        status, content = request("GET", f"/api/jobs/{job_id}")
        assert status == 200
        job = json.loads(content)
        job_status = job["status"]
        print(f"Status: {job_status}")
        if job_status in ["succeeded", "failed"]:
            break
        time.sleep(1)

    if job["status"] != "succeeded":
        print("Job failed or timed out")
        print(job)
        sys.exit(1)

    print("Checking artifacts...")
    status, content = request("GET", "/api/artifacts")
    assert status == 200
    artifacts = json.loads(content)
    assert len(artifacts) > 0
    art = artifacts[0]
    print(f"Artifact found: {art['id']}")

    # Download artifact
    print("Downloading MD artifact...")
    url = f"{BASE_URL}/api/artifacts/{art['id']}/download?key=md"
    try:
        with urllib.request.urlopen(url) as response:
            assert response.getcode() == 200
            content = response.read()
        print("MD content length:", len(content))
    except urllib.error.HTTPError as e:
        print(f"Download failed: {e.code} {e.read()}")
        sys.exit(1)

    print("Tests passed!")

if __name__ == "__main__":
    run_tests()
