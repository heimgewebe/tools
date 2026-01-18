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

        # Robust Request Handler (Option B: Full Interception)
        def handle_request(route):
            url = route.request.url
            # Simple parsing for flat directory structure
            # In a real app with subdirs, this would need better logic or a real server.
            path = url.split("/")[-1].split("?")[0]

            # Root / Index
            if url.endswith(":8000/") or path == "index.html" or path == "":
                try:
                    with open(os.path.join(UI_DIR, "index.html"), "r") as f:
                        content = f.read()
                    # Inject test build info
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
                # API Mocks (intercept specific API calls here if not handled by glob routes below)
                if "/api/" in url:
                    # Let the specific API routes handle it, or fallback to 404 if missed
                    route.fallback()
                else:
                    # STRICT 404 for unknown static files
                    # This prevents 'route.continue_()' from hitting the void
                    route.fulfill(status=404, body="Not Found")

        # Set up routing
        # Note: We use a broad pattern but will fallback for API routes
        # Playwright routing priority: First matching handler wins?
        # Actually, Playwright matches in order of registration (last registered wins?) or first?
        # Docs say: "Routes are matched in the order they are registered."
        # So we register specific API routes FIRST, then the catch-all.

        # 1. API Mocks
        page.route("**/api/version", lambda route: route.fulfill(json={"version": "verify-tool", "build_id": "v1"}))
        page.route("**/api/health", lambda route: route.fulfill(json={"status": "ok", "hub": "/mock/hub", "merges_dir": "/mock/merges"}))
        page.route("**/api/artifacts", lambda route: route.fulfill(json=[]))
        page.route("**/api/repos*", lambda route: route.fulfill(json=["repoA", "repoB"]))
        page.route("**/api/jobs", lambda route: route.fulfill(json={"id": "job-tool-1", "status": "queued"}))

        # 2. Static / Catch-all
        page.route("**/*", handle_request)

        # Inject pool state
        pool_state = {
            "repoA": {"raw": None, "compressed": None},
            "repoB": {"raw": ["fileB.txt"], "compressed": ["fileB.txt"]}
        }

        try:
            page.goto("http://localhost:8000/")

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
