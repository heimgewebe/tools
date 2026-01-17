import pytest
from playwright.sync_api import Page, Route, expect
import json
import os
import time

UI_DIR = os.path.abspath("merger/lenskit/frontends/webui")

@pytest.fixture
def page_with_static(page: Page):
    # Log console
    page.on("console", lambda msg: print(f"PAGE LOG: {msg.text}"))
    page.on("pageerror", lambda exc: print(f"PAGE ERROR: {exc}"))

    with open(os.path.join(UI_DIR, "index.html"), "r") as f:
        content = f.read()

    content = content.replace("__RLENS_ASSET_BASE__", "./")
    content = content.replace("__RLENS_BUILD__", "test-v1")

    page.route("http://localhost:8000/", lambda route: route.fulfill(
        status=200,
        body=content,
        content_type="text/html"
    ))

    def handle_static(route: Route):
        path = route.request.url.split("/")[-1].split("?")[0]
        file_path = os.path.join(UI_DIR, path)
        if os.path.exists(file_path):
            content_type = "text/plain"
            if path.endswith(".js"):
                content_type = "application/javascript"
            elif path.endswith(".css"):
                content_type = "text/css"
            elif path.endswith(".html"):
                content_type = "text/html"

            with open(file_path, "rb") as f:
                route.fulfill(body=f.read(), content_type=content_type)
        else:
            route.continue_()

    page.route("**/app.js*", handle_static)
    page.route("**/style.css*", handle_static)

    page.route("**/api/version", lambda route: route.fulfill(json={"version": "test", "build_id": "test-1"}))
    page.route("**/api/health", lambda route: route.fulfill(json={"status": "ok", "hub": "/mock/hub", "merges_dir": "/mock/merges"}))
    page.route("**/api/artifacts", lambda route: route.fulfill(json=[]))
    page.route("**/api/repos*", lambda route: route.fulfill(json=["repoA", "repoB"]))

    return page

def test_run_merge_picks_up_pool_selections(page_with_static: Page):
    """
    Verifies that the 'Run Merge' button correctly picks up pool selections
    and uses Combined Job Mapping (strict_include_paths_by_repo) when partial selections exist.
    """
    pool_state = {
        "repoA": {"raw": None, "compressed": None}, # Full selection
        "repoB": {"raw": ["fileB.txt"], "compressed": ["fileB.txt"]} # Partial selection
    }

    # Enable Test Hook
    page_with_static.add_init_script("window.__RLENS_TEST__ = true;")

    page_with_static.goto("http://localhost:8000/")

    # Inject state
    page_with_static.evaluate(f"""
        const pool = {json.dumps(pool_state)};
        localStorage.setItem("lenskit.prescan.savedSelections.v1", JSON.stringify(pool));
    """)

    # Reload to pick up state
    page_with_static.reload()

    # Wait for pool to be initialized using explicit signal
    page_with_static.wait_for_function("() => window.__rlens_pool_ready === true")

    # Wait for repos to load (badge logic might take a moment to render)
    page_with_static.wait_for_selector("#repoList input[name='repos']")

    # Select both repos in the list
    page_with_static.evaluate("""
        const boxes = document.querySelectorAll('input[name="repos"]');
        boxes.forEach(b => b.checked = true);
    """)

    payloads = []
    def handle_jobs(route: Route):
        if route.request.method == "POST":
            data = route.request.post_data_json
            if data is None:
                data = json.loads(route.request.post_data)
            payloads.append(data)
            route.fulfill(json={"id": "job-" + str(len(payloads)), "status": "queued"})
        else:
            route.continue_()

    page_with_static.route("**/api/jobs", handle_jobs)

    # Set mode to 'gesamt' (Combined)
    page_with_static.select_option("#mode", "gesamt")

    # Click Run Merge (Main Form Submit)
    page_with_static.click("#jobForm button[type='submit']")

    # Explicitly wait for the request to be captured
    def wait_for_payloads():
        start = time.time()
        while time.time() - start < 5:
            if len(payloads) == 1:
                return
            page_with_static.wait_for_timeout(50)
        raise TimeoutError(f"Payloads count {len(payloads)} != 1")

    wait_for_payloads()

    assert len(payloads) == 1
    p = payloads[0]

    # Verify Combined Job Structure
    assert sorted(p["repos"]) == ["repoA", "repoB"]

    # Check for mapping
    assert "include_paths_by_repo" in p
    ipbr = p["include_paths_by_repo"]
    assert ipbr["repoA"] is None # Full
    assert ipbr["repoB"] == ["fileB.txt"] # Partial

    # Check strict flag
    assert p.get("strict_include_paths_by_repo") is True

    # Check that generic include_paths is NOT set
    assert "include_paths" not in p or p["include_paths"] is None


def test_run_merge_combined_when_no_partial_pool(page_with_static: Page):
    """
    Verifies that 'Run Merge' keeps Combined mode if there are no partial pool selections.
    """
    pool_state = {
        "repoA": {"raw": None, "compressed": None}, # Full
        # RepoB not in pool (Standard behavior = Full)
    }

    page_with_static.add_init_script("window.__RLENS_TEST__ = true;")
    page_with_static.goto("http://localhost:8000/")

    page_with_static.evaluate(f"""
        const pool = {json.dumps(pool_state)};
        localStorage.setItem("lenskit.prescan.savedSelections.v1", JSON.stringify(pool));
    """)
    page_with_static.reload()

    page_with_static.wait_for_function("() => window.__rlens_pool_ready === true")
    page_with_static.wait_for_selector("#repoList input[name='repos']")

    page_with_static.evaluate("""
        const boxes = document.querySelectorAll('input[name="repos"]');
        boxes.forEach(b => b.checked = true);
    """)

    payloads = []
    def handle_jobs(route: Route):
        if route.request.method == "POST":
            data = route.request.post_data_json
            if data is None:
                data = json.loads(route.request.post_data)
            payloads.append(data)
            route.fulfill(json={"id": "job-123", "status": "queued"})
        else:
            route.continue_()

    page_with_static.route("**/api/jobs", handle_jobs)

    page_with_static.select_option("#mode", "gesamt")

    # Click Run Merge
    page_with_static.click("#jobForm button[type='submit']")

    def wait_for_payload():
        start = time.time()
        while time.time() - start < 5:
            if len(payloads) > 0:
                return
            page_with_static.wait_for_timeout(50)
        raise TimeoutError("Payload not captured")

    wait_for_payload()

    assert len(payloads) == 1
    p = payloads[0]

    assert sorted(p["repos"]) == ["repoA", "repoB"]
    assert "include_paths" not in p or p["include_paths"] is None
    assert "include_paths_by_repo" not in p
