import json
import argparse
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException

def init_driver():
    options = Options()
    options.headless = True
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(15)
    return driver

def is_root_url(url):
    """Return True if URL is a root domain with no path."""
    parsed = urlparse(url)
    return parsed.path in ("", "/")

def is_404_page(driver):
    """Check for 404 indicators in title or body text."""
    title = driver.title.lower()
    body_text = driver.find_element("tag name", "body").text.lower()
    if "404" in title or "not found" in title:
        return True
    if "404" in body_text or "not found" in body_text:
        return True
    return False

def check_url_selenium(driver, url):
    """
    Check if a URL is valid:
    - Loads without error
    - Not a 404 page
    - Not redirected to a root domain
    """
    try:
        driver.get(url)
        # 1️⃣ Check if page is 404
        if is_404_page(driver):
            print(f"Page returned 404: {url}")
            return False
        # 2️⃣ Check if current URL after redirects is a root URL
        final_url = driver.current_url
        if is_root_url(final_url):
            print(f"Redirected to root URL (invalid): {final_url}")
            return False
        return True
    except (WebDriverException, TimeoutException) as e:
        print(f"Error accessing URL {url}: {e}")
        return False

def process_event(event, driver, invalid_urls):
    url = event.get("Url")
    if url:
        is_valid = check_url_selenium(driver, url)
        event["url_valid"] = is_valid
        if not is_valid:
            invalid_urls.append(url)
        return is_valid
    return False

def process_jsonl_file(file_path):
    total_urls = 0
    valid_urls = 0
    invalid_urls = []

    driver = init_driver()

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_data = json.loads(line)

            if line_data.get("status") != "success":
                continue

            events = line_data.get("events", [])
            for event in events:
                total_urls += 1
                if process_event(event, driver, invalid_urls):
                    valid_urls += 1

    driver.quit()

    # Summary
    print("\n=== URL Validation Summary ===")
    print(f"Total URLs processed: {total_urls}")
    print(f"Valid URLs (loaded successfully): {valid_urls}")
    print(f"Invalid URLs: {len(invalid_urls)}")
    if invalid_urls:
        print("\nList of invalid URLs:")
        for url in invalid_urls:
            print(url)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate URLs in JSONL file events using Selenium")
    parser.add_argument("file_path", type=str, help="Path to the JSONL file")
    args = parser.parse_args()

    process_jsonl_file(args.file_path)