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

    print("Checking health (no auth)...")
    r = requests.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["auth_enabled"] == True
    print("Health check OK, Auth enabled")

    print("Checking repos without token (expect 403/401)...")
    r = requests.get(f"{BASE_URL}/api/repos")
    assert r.status_code == 401
    print("Access denied as expected")

    headers = {"Authorization": "Bearer secret123"}
    print("Checking repos WITH token...")
    r = requests.get(f"{BASE_URL}/api/repos", headers=headers)
    assert r.status_code == 200
    print("Access granted")

    # Path Traversal Test (implicit via allowlist)
    # create job with path outside Hub
    print("Creating job with invalid hub path...")
    payload = {
        "hub": "/etc",
        "repos": None
    }
    r = requests.post(f"{BASE_URL}/api/jobs", json=payload, headers=headers)
    if r.status_code == 403:
        print("Blocked access to /etc as expected")
    else:
        # If /etc doesn't exist or is not a dir, it might fail differently in validation
        # But we expect the Allowlist to catch it first if validate_hub_path is called.
        # But create_job calls validate_hub_path ONLY if hub is passed.
        # If /etc is not in allowlist (which is just HUB), it should fail.
        print(f"Response: {r.status_code} {r.text}")
        # Note: If running in container, /etc exists.
        assert r.status_code == 403

    print("Tests passed!")

if __name__ == "__main__":
    run_tests()
