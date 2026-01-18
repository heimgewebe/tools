from playwright.sync_api import sync_playwright
import os
import json

UI_DIR = os.path.abspath("merger/lenskit/frontends/webui")

def verify_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Mock static files
        def handle_static(route):
            path = route.request.url.split("/")[-1].split("?")[0]
            if path == "": path = "index.html"

            # Handle base path replacements for index.html
            if path == "index.html" or route.request.url.endswith(":8000/"):
                with open(os.path.join(UI_DIR, "index.html"), "r") as f:
                    content = f.read()
                content = content.replace("__RLENS_ASSET_BASE__", "./")
                content = content.replace("__RLENS_BUILD__", "verify-v1")
                route.fulfill(body=content, content_type="text/html")
                return

            file_path = os.path.join(UI_DIR, path)
            if os.path.exists(file_path):
                content_type = "text/plain"
                if path.endswith(".js"): content_type = "application/javascript"
                elif path.endswith(".css"): content_type = "text/css"
                elif path.endswith(".html"): content_type = "text/html"

                with open(file_path, "rb") as f:
                    route.fulfill(body=f.read(), content_type=content_type)
            else:
                route.continue_()

        page.route("**/*", handle_static)

        # Mock API
        page.route("**/api/version", lambda route: route.fulfill(json={"version": "verify", "build_id": "v1"}))
        page.route("**/api/health", lambda route: route.fulfill(json={"status": "ok", "hub": "/mock/hub", "merges_dir": "/mock/merges"}))
        page.route("**/api/artifacts", lambda route: route.fulfill(json=[]))
        page.route("**/api/repos*", lambda route: route.fulfill(json=["repoA", "repoB"]))
        page.route("**/api/jobs", lambda route: route.fulfill(json={"id": "job-1", "status": "queued"}))

        # Inject pool state
        pool_state = {
            "repoA": {"raw": None, "compressed": None},
            "repoB": {"raw": ["fileB.txt"], "compressed": ["fileB.txt"]}
        }

        page.goto("http://localhost:8000/")

        # Set local storage and reload to trigger pool UI
        page.evaluate(f"""
            const pool = {json.dumps(pool_state)};
            localStorage.setItem("lenskit.prescan.savedSelections.v1", JSON.stringify(pool));
        """)
        page.reload()

        # Wait for UI to settle
        page.wait_for_selector("#repoList input[name='repos']")

        # Wait for potential pool UI elements
        page.wait_for_timeout(1000)

        # Verify "Run Merge from Pool" is GONE
        # We search for a button that might have that text
        pool_btn = page.query_selector("button:has-text('Run Merge from Pool')")
        if pool_btn:
             print("FAILURE: 'Run Merge from Pool' button found!")
        else:
             print("SUCCESS: 'Run Merge from Pool' button NOT found.")

        # Verify "Start Job" is present
        start_btn = page.query_selector("#jobForm button[type='submit']")
        if start_btn:
            print("SUCCESS: 'Start Job' button found.")
        else:
            print("FAILURE: 'Start Job' button NOT found.")

        # Take screenshot
        page.screenshot(path="verification/verification.png", full_page=True)
        print("Screenshot saved to verification/verification.png")

        browser.close()

if __name__ == "__main__":
    verify_ui()
