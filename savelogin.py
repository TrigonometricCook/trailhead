from playwright.sync_api import sync_playwright

def initialize():
    with sync_playwright() as p:
        # Path to your empty folder
        user_data_dir = "D:/playwright_data"

        print("Opening browser for initialization...")
        
        # Launching persistent context
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            channel="chrome"  # Uses your installed Chrome
        )
        
        page = context.pages[0]
        
        # Go to the Trailhead login page
        page.goto("https://trailhead.salesforce.com/login/")
        
        print("\n--- ACTION REQUIRED ---")
        print("1. Log in manually in the browser window.")
        print("2. Complete any 2FA (email codes, etc.).")
        print("3. Once you see your Trailhead Dashboard, come back here.")
        
        # This keeps the browser open until you manually close it
        # Or until you press Enter in the terminal
        input("\nPress Enter here in the terminal ONLY AFTER you have logged in and see your dashboard...")
        
        print("Closing browser and saving session data to D:/playwright_data...")
        context.close()

if __name__ == "__main__":
    initialize()