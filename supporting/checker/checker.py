import json
import argparse
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException, StaleElementReferenceException
from tqdm import tqdm

def init_driver():
    options = Options()
    options.headless = True
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    prefs = {
        "profile.managed_default_content_settings.images": 2,  # block images
        "profile.default_content_setting_values.stylesheets": 2,  # block CSS
        "profile.managed_default_content_settings.cookies": 2,  # optional
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

def is_root_url(url):
    parsed = urlparse(url)
    return parsed.path in ("", "/")

def is_404_page(driver):
    """Safely check for 404, handling stale elements."""
    try:
        title = driver.title.lower()
        body_text = driver.find_element("tag name", "body").text.lower()
        return "404" in title or "404" in body_text
    except StaleElementReferenceException:
        return False
    except Exception:
        return False

def check_url_selenium(url):
    driver = None
    try:
        driver = init_driver()
        driver.get(url)
        # 404 check
        if is_404_page(driver):
            return False, "404 page detected"
        # Root URL after redirects
        final_url = driver.current_url
        if is_root_url(final_url):
            return False, f"Redirected to root URL ({final_url})"
        return True, None
    except (WebDriverException, TimeoutException) as e:
        return False, str(e)
    finally:
        if driver:
            driver.quit()

def process_event(event):
    """Process an event only if score > 0.4."""
    score = event.get("score", 0)
    if score <= 0.4:
        return None, False, "Score too low"
    url = event.get("Url")
    if not url:
        return None, False, "No URL"
    is_valid, error_msg = check_url_selenium(url)
    event["url_valid"] = is_valid
    return url, is_valid, error_msg

def process_jsonl_file(file_path, max_workers=4):
    invalid_urls = []
    valid_urls = 0

    # Gather events with score > 0.4
    urls_to_check = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_data = json.loads(line)
            if line_data.get("status") != "success":
                continue
            for event in line_data.get("events", []):
                if event.get("score", 0) > 0.4:
                    urls_to_check.append(event)

    total_urls = len(urls_to_check)

    # ThreadPoolExecutor with tqdm progress bar
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_event = {executor.submit(process_event, e): e for e in urls_to_check}
        for future in tqdm(as_completed(future_to_event), total=total_urls, desc="Checking URLs"):
            url, is_valid, error_msg = future.result()
            if not is_valid and url:
                invalid_urls.append((url, error_msg))
            else:
                valid_urls += 1

    # Summary
    if invalid_urls:
        print("\nList of invalid URLs and reasons:")
        for url, err in invalid_urls:
            print(f"{url} --> {err}")
    print("\n=== URL Validation Summary ===")
    print(f"Total URLs processed: {total_urls}")
    print(f"Valid URLs (loaded successfully): {valid_urls}")
    print(f"Invalid URLs: {len(invalid_urls)}")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate URLs in JSONL file events using Selenium")
    parser.add_argument("file_path", type=str, help="Path to the JSONL file")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel Selenium workers")
    args = parser.parse_args()

    process_jsonl_file(args.file_path, max_workers=args.workers)