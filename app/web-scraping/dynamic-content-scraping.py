from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import os

BASE_DOMAIN = "www.madewithnestle.ca"
START_URL = f"https://{BASE_DOMAIN}"
visited = set()
scraped_data = []
failed_urls = []
save_batch_size = 20
file_index = 1

def is_internal_link(url):
    return urlparse(url).netloc in ("", BASE_DOMAIN)

def normalize_url(base, link):
    return urljoin(base, link.split('#')[0])  # Remove anchors

def scrape_page(page, url):
    print(f"[+] Scraping: {url}")
    page.goto(url, timeout=60000)
    page.wait_for_load_state('networkidle')
    time.sleep(3)

    soup = BeautifulSoup(page.content(), 'html.parser')

    text = soup.get_text(separator='\n')
    links = [normalize_url(url, a['href']) for a in soup.find_all('a', href=True)]
    images = [(img['src'], img.get('alt', '')) for img in soup.find_all('img') if 'src' in img.attrs]

    return {
        'url': url,
        'text': text.strip(),
        'links': links,
        'images': images
    }

def save_scraped_batch(batch_data, batch_index):
    filename = f"madewithnestle_scraped_{batch_index}.json"
    with open(filename, "w") as f:
        json.dump(batch_data, f, indent=2)
    print(f"[✔] Saved batch {batch_index} to {filename}")

def save_failed_urls(failed_list):
    with open("madewithnestle_failed_urls.txt", "w") as f:
        for url in failed_list:
            f.write(url + "\n")
    print(f"[!] Saved failed URLs to madewithnestle_failed_urls.txt")

def crawl_site(start_url):
    global file_index
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        to_visit = [start_url]

        while to_visit:
            current_url = to_visit.pop()
            if current_url in visited or not current_url.startswith("http"):
                continue
            visited.add(current_url)

            try:
                data = scrape_page(page, current_url)
                scraped_data.append(data)

                # Save batch every 20 pages
                if len(scraped_data) % save_batch_size == 0:
                    save_scraped_batch(scraped_data, file_index)
                    file_index += 1
                    scraped_data.clear()

                # Queue internal links
                for link in data['links']:
                    if is_internal_link(link) and link not in visited:
                        to_visit.append(link)

            except Exception as e:
                print(f"[!] Failed to scrape {current_url}: {e}")
                failed_urls.append(current_url)

        browser.close()

        # Save remaining pages
        if scraped_data:
            save_scraped_batch(scraped_data, file_index)

        # Save any failed URLs
        if failed_urls:
            save_failed_urls(failed_urls)

        print(f"\n✅ Finished. Total visited: {len(visited)} | Failed: {len(failed_urls)}")

if __name__ == "__main__":
    crawl_site(START_URL)
