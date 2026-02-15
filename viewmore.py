import time
import csv
import os
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
USER_DATA_DIR = "D:/playwright_data"
SEARCH_URL = "https://trailhead.salesforce.com/search/learning?tab=LEARNING&sort=MOST_POINTS&content_type=badge&assessments_include_hoc=false&progress=INCOMPLETE&keywords=mail"
OUTPUT_FILE = "trail_sublinks3.csv"

def crawl_inner_page(context, url, parent_title, csv_writer, file_handle):
    """Navigates to a specific module/trail page, extracts internal links, and saves."""
    print(f"\n>>> DEEP CRAWL: Entering '{parent_title}'")
    inner_page = context.new_page()
    try:
        inner_page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Using the simplified link detection from the solver program
        inner_links = inner_page.locator("a[href*='/modules/'], a[href*='/units/']").all()
        
        found_count = 0
        for link in inner_links:
            href = link.get_attribute("href")
            if href:
                inner_title = link.inner_text().strip()
                if not inner_title: continue
                
                full_inner_url = href if href.startswith("http") else f"https://trailhead.salesforce.com{href}"
                csv_writer.writerow([parent_title, url, inner_title, full_inner_url])
                file_handle.flush() 
                print(f"    [SAVED] {inner_title}")
                found_count += 1
    except Exception as e:
        print(f"    ❌ Error crawling inner page: {e}")
    finally:
        inner_page.close()

def run_crawler():
    file_exists = os.path.isfile(OUTPUT_FILE)
    extracted_main_urls = set()

    with open(OUTPUT_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Parent Title", "Parent URL", "Sub-Link Title", "Sub-Link URL"])

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                USER_DATA_DIR, headless=False, channel="chrome", args=["--start-maximized"]
            )
            
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(SEARCH_URL, wait_until="networkidle")

            while True:
                # Using the search logic from the second program (Role-based)
                # This targets the specific badge links found in search results
                badges = page.locator("a[href*='/content/learn/']").all()
                new_links_to_process = []

                for badge in badges:
                    try:
                        href = badge.get_attribute("href")
                        if href and href not in extracted_main_urls:
                            # Using the title logic from the second program
                            title = badge.inner_text().strip() or "Untitled"
                            full_url = href if href.startswith("http") else f"https://trailhead.salesforce.com{href}"
                            new_links_to_process.append((full_url, title))
                            extracted_main_urls.add(href)
                    except: continue

                # Deep crawl each found badge
                for url, title in new_links_to_process:
                    crawl_inner_page(context, url, title, writer, f)

                # --- VIEW MORE LOGIC (USING ARIA ROLE FROM SECOND PROGRAM) ---
                view_more_btn = page.get_by_role("button", name="View More")
                
                if view_more_btn.is_visible():
                    print(f"LOG: Clicking 'View More' via Role identification")
                    view_more_btn.click()
                    # Using the simple sleep from the second program as requested
                    time.sleep(5) 
                else:
                    print("No more 'View More' button found.")
                    break
                    
            context.close()

if __name__ == "__main__":
    run_crawler()