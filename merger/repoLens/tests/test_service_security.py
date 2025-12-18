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
                try:
                    return response.status, json.loads(body)
                except:
                    return response.status, body
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

    token = "secret123"

    # Path Traversal Test via Hub
    print("Test 1: Invalid Hub Path (traversal)...")
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

    # Repo Traversal Test
    print("Test 2: Invalid Repo Name (traversal)...")
    payload = {
        "repos": ["../etc"],
        "level": "max"
    }
    status, resp = make_request("/api/jobs", method="POST", data=payload, token=token)
    if status == 400:
        print("Blocked invalid repo name as expected")
    else:
        print(f"Unexpected status: {status} {resp}")
        assert status == 400

    # Happy Path Job
    print("Test 3: Valid Job...")
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

    # Verify log streaming via FILE (implicit check if endpoint works)
    print("Test 4: Log Streaming...")
    # Using simple GET with query token for SSE simulation
    log_url = f"{BASE_URL}/api/jobs/{job_id}/logs?token={token}"
    try:
        with urllib.request.urlopen(log_url) as response:
            assert response.status == 200
            # Read a bit
            chunk = response.read(100)
            if chunk:
                print("Received log chunk")
            else:
                print("Warning: Empty log stream?")
    except Exception as e:
        print(f"Log stream failed: {e}")
        sys.exit(1)

    print("Tests passed!")

if __name__ == "__main__":
    run_tests()
