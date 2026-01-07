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
            with open(file_path, "rb") as f:
                route.fulfill(body=f.read())
        else:
            route.continue_()

    page.route("**/app.js*", handle_static)
    page.route("**/style.css*", handle_static)

    page.route("**/api/version", lambda route: route.fulfill(json={"version": "test", "build_id": "test-1"}))
    page.route("**/api/health", lambda route: route.fulfill(json={"status": "ok", "hub": "/mock/hub", "merges_dir": "/mock/merges"}))
    page.route("**/api/artifacts", lambda route: route.fulfill(json=[]))
    page.route("**/api/repos*", lambda route: route.fulfill(json=["repoA", "repoB"]))

    return page

def test_pool_payload_combined(page_with_static: Page):
    pool_state = {
        "repoA": {"raw": None, "compressed": None},
        "repoB": {"raw": ["fileB.txt"], "compressed": ["fileB.txt"]}
    }

    page_with_static.goto("http://localhost:8000/")

    # Inject state
    page_with_static.evaluate(f"""
        const pool = {json.dumps(pool_state)};
        localStorage.setItem("lenskit.prescan.savedSelections.v1", JSON.stringify(pool));
    """)

    # Reload to pick up state
    page_with_static.reload()

    # Check if pool loaded
    size = page_with_static.evaluate("() => savedPrescanSelections.size")
    print(f"DEBUG: Pool Size: {size}")

    payloads = []
    def handle_jobs(route: Route):
        if route.request.method == "POST":
            payloads.append(route.request.post_data_json)
            route.fulfill(json={"id": "job-123", "status": "queued"})
        else:
            route.continue_()

    page_with_static.route("**/api/jobs", handle_jobs)

    page_with_static.select_option("#mode", "gesamt")

    # Force Show Panel via JS to avoid UI flakiness
    page_with_static.evaluate("""
        document.getElementById('selectionPool').classList.remove('hidden');
        renderSelectionPool();
    """)

    # Click Run
    page_with_static.click("#selectionPool button:has-text('Run Merge from Pool')")

    page_with_static.wait_for_timeout(500)

    assert len(payloads) == 1
    p = payloads[0]

    assert sorted(p["repos"]) == ["repoA", "repoB"]
    ipbr = p["include_paths_by_repo"]
    assert ipbr["repoA"] is None
    assert ipbr["repoB"] == ["fileB.txt"]
    assert p.get("strict_include_paths_by_repo") is True
    assert "include_paths" not in p or p["include_paths"] is None


def test_pool_payload_pro_repo(page_with_static: Page):
    pool_state = {
        "repoA": {"raw": None, "compressed": None},
        "repoB": {"raw": ["fileB.txt"], "compressed": ["fileB.txt"]}
    }

    page_with_static.goto("http://localhost:8000/")

    page_with_static.evaluate(f"""
        localStorage.setItem("lenskit.prescan.savedSelections.v1", JSON.stringify({json.dumps(pool_state)}));
    """)
    page_with_static.reload()

    size = page_with_static.evaluate("() => savedPrescanSelections.size")
    print(f"DEBUG: Pool Size: {size}")

    payloads = []
    page_with_static.route("**/api/jobs", lambda r: (payloads.append(r.request.post_data_json), r.fulfill(json={"id": "job-"+str(len(payloads)), "status": "queued"}))[1])

    page_with_static.select_option("#mode", "pro-repo")

    # Force Show Panel via JS
    page_with_static.evaluate("""
        document.getElementById('selectionPool').classList.remove('hidden');
        renderSelectionPool();
    """)

    page_with_static.click("#selectionPool button:has-text('Run Merge from Pool')")

    page_with_static.wait_for_timeout(500)

    assert len(payloads) == 2
    repos_seen = set()
    for p in payloads:
        assert len(p["repos"]) == 1
        repo = p["repos"][0]
        repos_seen.add(repo)
        if repo == "repoA":
            assert "include_paths" not in p or p["include_paths"] is None
        elif repo == "repoB":
            assert p["include_paths"] == ["fileB.txt"]
        assert "include_paths_by_repo" not in p

    assert repos_seen == {"repoA", "repoB"}
