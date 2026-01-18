from playwright.sync_api import sync_playwright
import os
import json
import sys

# Determine the project root and UI directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_DIR = os.path.join(PROJECT_ROOT, "merger/lenskit/frontends/webui")

def verify_ui():
    """
    Verifies that the redundant 'Run Merge from Pool' button is gone
    and the main 'Start Job' button is present.
    """
    print(f"Starting UI verification against {UI_DIR}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Robust Request Handler (Strict Mode)
        def handle_request(route):
            url = route.request.url
            path = url.split("/")[-1].split("?")[0]

            # Root / Index
            # Matches http://verify.local/ or index.html
            if url == "http://verify.local/" or path == "index.html" or path == "":
                try:
                    with open(os.path.join(UI_DIR, "index.html"), "r") as f:
                        content = f.read()
                    content = content.replace("__RLENS_ASSET_BASE__", "./")
                    content = content.replace("__RLENS_BUILD__", "verify-tool-v1")
                    route.fulfill(body=content, content_type="text/html")
                except Exception as e:
                    print(f"Error serving index: {e}")
                    route.fulfill(status=500, body=str(e))
                return

            # Static Files
            file_path = os.path.join(UI_DIR, path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                content_type = "text/plain"
                if path.endswith(".js"): content_type = "application/javascript"
                elif path.endswith(".css"): content_type = "text/css"
                elif path.endswith(".html"): content_type = "text/html"

                with open(file_path, "rb") as f:
                    route.fulfill(body=f.read(), content_type=content_type)
            else:
                # STRICT 404 for everything else.
                # No fallback to network.
                route.fulfill(status=404, body="Not Found")

        # 0. Global Route Interception (Prevent DNS/Network for fake domain)
        # This is critical: We must intercept EVERYTHING for http://verify.local/
        # BEFORE any other specific mocks if we want to be safe, OR rely on the fact that
        # specific mocks match first. But to prevent "ERR_NAME_NOT_RESOLVED", we must ensure
        # the network layer never actually tries to resolve "verify.local".
        # Playwright's `route("**/*", ...)` intercepts all requests.

        # We need a unified handler that delegates to either API mocks or Static/Index.
        # This avoids ordering ambiguity and ensures total interception.

        def master_handler(route):
            url = route.request.url

            # API Routing
            if "/api/version" in url:
                route.fulfill(json={"version": "verify-tool", "build_id": "v1"})
                return
            if "/api/health" in url:
                route.fulfill(json={"status": "ok", "hub": "/mock/hub", "merges_dir": "/mock/merges"})
                return
            if "/api/artifacts" in url:
                route.fulfill(json=[])
                return
            if "/api/repos" in url:
                route.fulfill(json=["repoA", "repoB"])
                return
            if "/api/jobs" in url:
                route.fulfill(json={"id": "job-tool-1", "status": "queued"})
                return

            # Static/Index Routing
            handle_request(route)

        page.route("**/*", master_handler)

        # Inject pool state
        pool_state = {
            "repoA": {"raw": None, "compressed": None},
            "repoB": {"raw": ["fileB.txt"], "compressed": ["fileB.txt"]}
        }

        try:
            # Use fictitious domain to avoid localhost networking issues
            page.goto("http://verify.local/")

            # Set local storage and reload
            page.evaluate(f"""
                const pool = {json.dumps(pool_state)};
                localStorage.setItem("lenskit.prescan.savedSelections.v1", JSON.stringify(pool));
            """)
            page.reload()

            # Wait for UI
            page.wait_for_selector("#repoList input[name='repos']")
            page.wait_for_timeout(500)

            # Verification Logic
            failed = False

            # 1. Check for redundant button
            pool_btn = page.query_selector("button:has-text('Run Merge from Pool')")
            if pool_btn:
                print("FAILURE: 'Run Merge from Pool' button found!")
                failed = True
            else:
                print("SUCCESS: 'Run Merge from Pool' button NOT found.")

            # 2. Check for main button
            start_btn = page.query_selector("#jobForm button[type='submit']")
            if start_btn:
                print("SUCCESS: 'Start Job' button found.")
            else:
                print("FAILURE: 'Start Job' button NOT found.")
                failed = True

            if failed:
                sys.exit(1)

            print("Verification passed.")

        except Exception as e:
            print(f"Verification crashed: {e}")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    verify_ui()
