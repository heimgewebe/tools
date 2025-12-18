import urllib.request
import urllib.error
import json
import time
import sys
import os

BASE_URL = "http://127.0.0.1:9999"

def wait_for_server():
    for _ in range(10):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health") as response:
                if response.status == 200:
                    return True
        except urllib.error.URLError:
            time.sleep(1)
        except Exception:
            time.sleep(1)
    return False

def make_request(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    if data:
        json_data = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
        req.data = json_data

    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            if body:
                return response.status, json.loads(body)
            return response.status, None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        # try parse json
        try:
            return e.code, json.loads(body)
        except:
            return e.code, body

def run_tests():
    print(f"Waiting for server at {BASE_URL}...")
    if not wait_for_server():
        print("Server did not start")
        sys.exit(1)

    print("Checking health (no auth)...")
    status, data = make_request("/api/health")
    assert status == 200
    assert data["auth_enabled"] == True
    print("Health check OK, Auth enabled")

    print("Checking repos without token (expect 401)...")
    status, _ = make_request("/api/repos")
    assert status == 401
    print("Access denied as expected")

    token = "secret123"
    print("Checking repos WITH token...")
    status, repos = make_request("/api/repos", token=token)
    assert status == 200
    print("Access granted")

    # Path Traversal Test
    print("Creating job with invalid hub path...")
    payload = {
        "hub": "/etc",
        "repos": None
    }
    status, resp = make_request("/api/jobs", method="POST", data=payload, token=token)
    if status == 403:
        print("Blocked access to /etc as expected")
    else:
        print(f"Unexpected status: {status} {resp}")
        assert status == 403

    # Happy Path Job
    print("Creating valid job...")
    payload = {
        "repos": ["tests"], # assuming 'tests' exists in hub (merger/repoLens)
        "level": "max",
        "plan_only": True
    }
    status, job = make_request("/api/jobs", method="POST", data=payload, token=token)
    assert status == 200
    job_id = job["id"]
    print(f"Job created: {job_id}")

    # Poll
    for _ in range(20):
        status, job = make_request(f"/api/jobs/{job_id}", token=token)
        if job["status"] in ["succeeded", "failed"]:
            break
        time.sleep(1)

    assert job["status"] == "succeeded"
    print("Job succeeded")

    # Check latest
    print("Checking latest artifact...")
    # Wait a bit for artifact registration? Should be done if job succeeded.
    status, art = make_request(f"/api/artifacts/latest?repo=tests&level=max&mode=gesamt", token=token)
    assert status == 200
    print(f"Latest artifact: {art['id']}")

    print("Tests passed!")

if __name__ == "__main__":
    run_tests()
