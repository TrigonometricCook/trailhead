import csv
import os
import re
import time
from playwright.sync_api import sync_playwright
from google import genai

# --- CONFIGURATION ---
SERVICE_ACCOUNT_PATH = r"D:\Trailhead\replace-service-acc-here.json" #path to service account
PROJECT_ID = "replace-project-id" #replace with the project id
LOCATION = "us-central1"
USER_DATA_DIR = "D:/playwright_data" #the folder where the login info is saved by savelogin.py
INPUT_FILE = "unique.csv"
OUTPUT_FILE = "trail_solve_status.csv"

# Auth Setup
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_PATH
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

def get_answers_from_ai(quiz_text):
    """Sends sanitized text to AI and returns cleaned list of letters (A-E)."""
    clean_text = " ".join(quiz_text.split())[:10000]
    prompt = f"Act as a Salesforce expert. Provide ONLY the correct letters (A, B, C, D, or E). Format: A, B\n\nQuiz: {clean_text}"
    
    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        raw_result = response.text.strip().upper()
        clean_answers = re.findall(r'\b([A-E])\b', raw_result)
        print(f"LOG: AI Suggested: {clean_answers}")
        return clean_answers
    except Exception as e:
        print(f"❌ LOG: AI Error: {e}")
        return None

def solve_quiz(context, url):
    """Processes a single unit. Closes tab ONLY on 'No Quiz' or 'Click Failed'."""
    page = context.new_page()
    page.set_default_timeout(15000) 
    print(f"\n>>> [OPENING]: {url}")
    
    try:
        page.goto(url, wait_until="domcontentloaded")
        shadow_host = "th-enhanced-quiz >> th-tds-enhanced-quiz"
        
        # 1. Check for Quiz Presence
        try:
            page.wait_for_selector(f"{shadow_host} >> legend", state="visible", timeout=10000)
        except:
            print("⚠️ LOG: No quiz detected. Closing tab.")
            page.close()
            return "No Quiz"

        # 2. PRE-CHECK: Interactability check
        options_locator = page.locator(f"{shadow_host} >> div.option-letter")
        if options_locator.count() == 0:
            print("❌ ABORT: Options not found. Closing tab.")
            page.close()
            return "Click Failed"

        # 3. Scrape Data
        time.sleep(2)
        quiz_data = "\n".join(page.locator(f"{shadow_host} >> fieldset").all_inner_texts())
        
        # 4. Prompt AI
        answers = get_answers_from_ai(quiz_data)
        if not answers:
            return "AI Failed"

        # 5. Clicking
        try:
            for i, letter in enumerate(answers):
                selector = f"{shadow_host} >> div.option-letter:text-is('{letter}')"
                target = page.locator(selector).nth(i)
                target.scroll_into_view_if_needed(timeout=4000)
                target.click(force=True, timeout=4000)
                print(f"   [OK] Q{i+1}: {letter}")
        except Exception:
            print(f"❌ ABORT: Click failed. Closing tab.")
            page.close()
            return "Click Failed"

        # 6. Submit
        time.sleep(2.5)
        submit_btn = page.locator(f"{shadow_host} >> th-tds-button.footer-button")
        if "button_disabled" not in (submit_btn.get_attribute("class") or ""):
            submit_btn.click()
            print("🚀 LOG: Submitted!")
            time.sleep(2) # Give it a moment to process the click
            return "Success"
        else:
            print("⚠️ LOG: Submit button disabled.")
            return "Submit Disabled"

    except Exception as e:
        print(f"❌ LOG: Error: {e}")
        return "Error"

def run_batch():
    processed_urls = set()
    
    # Resume Logic
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Status") == "Success":
                    processed_urls.add(row.get("Sub-Link URL"))

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found!")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        tasks = list(csv.DictReader(f))

    with sync_playwright() as p:
        print("LOG: Starting Chrome session...")
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR, 
            headless=False, 
            channel="chrome", 
            slow_mo=400
        )

        for row in tasks:
            url = row.get("Sub-Link URL")
            if url in processed_urls:
                continue
            
            status = solve_quiz(context, url)
            row["Status"] = status

            # Immediate Log to CSV
            file_exists = os.path.isfile(OUTPUT_FILE)
            with open(OUTPUT_FILE, mode='a', newline='', encoding='utf-8') as out_f:
                writer = csv.DictWriter(out_f, fieldnames=list(row.keys()))
                if not file_exists: 
                    writer.writeheader()
                writer.writerow(row)
                out_f.flush()

        print("\n" + "="*60 + "\nBATCH COMPLETE - Closing browser automatically...\n" + "="*60)
        time.sleep(3) # Final pause so you can see the last result
        context.close() # This shuts down all tabs and the browser window

if __name__ == "__main__":

    run_batch()

