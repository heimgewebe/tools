from playwright.sync_api import sync_playwright, expect
import time

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Open UI with token
        page.goto("http://localhost:8900/?token=secret")

        # Wait for loading
        page.wait_for_timeout(1000)

        # 2. Check "Atlas" tab contains new default excludes
        page.click("#tab-atlas")
        page.wait_for_selector("#atlasExcludes")

        excludes = page.input_value("#atlasExcludes")
        print(f"Excludes: {excludes}")

        expected_items = [".ssh", ".local/share", "Downloads"]
        for item in expected_items:
            if item in excludes:
                print(f"Verified: {item} found in excludes")
            else:
                print(f"FAILED: {item} not found in excludes")

        # 3. Open Picker and check if Roots are loaded (Requires 403 checks validation)
        # We can't easily click "picker" without button selector, let's find it.
        # Button near #hubPath
        page.click("button[onclick=\"openPicker('atlasRoot')\"]")
        page.wait_for_selector("#pickerModal", state="visible")
        page.wait_for_selector("#pickerList > div") # Wait for roots to load

        # Take screenshot of picker
        page.screenshot(path="verification_picker.png")
        print("Screenshot saved to verification_picker.png")

        # Check if we see "SYSTEM" root (since we enabled RLENS_ALLOW_FS_ROOT=1)
        content = page.content()
        if "SYSTEM" in content:
            print("Verified: SYSTEM root is visible")
        else:
            print("FAILED: SYSTEM root not found (Root opt-in check)")

        browser.close()

if __name__ == "__main__":
    verify_frontend()
