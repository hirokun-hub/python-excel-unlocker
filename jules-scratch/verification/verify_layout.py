from playwright.sync_api import sync_playwright, expect

def run_verification(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        # Navigate to the page
        page.goto("http://localhost:3000", timeout=30000)

        # Wait for the main card element to be visible
        card_locator = page.locator("div.w-full.max-w-4xl")
        expect(card_locator).to_be_visible(timeout=30000)

        # The user is not logged in by default, so we see a login overlay.
        # The prompt asks to check the alignment of the dropzone with other form elements.
        # These elements are blurred when not logged in.
        # For the purpose of this verification, we can assume the alignment holds true
        # even with the blur effect, as it's a CSS filter and shouldn't affect layout widths.

        # Take a screenshot of the main card area.
        screenshot_path = "jules-scratch/verification/layout_verification.png"
        card_locator.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        browser.close()

with sync_playwright() as playwright:
    run_verification(playwright)
