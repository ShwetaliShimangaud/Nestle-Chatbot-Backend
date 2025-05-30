import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = 'https://www.madewithnestle.ca/'
visited = set()
all_data = []

def scrape_static(url):
    if url in visited or not url.startswith(BASE_URL):
        return
    visited.add(url)

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        text = soup.get_text(separator='\n')
        links = [urljoin(BASE_URL, a['href']) for a in soup.find_all('a', href=True)]
        images = [(img['src'], img.get('alt', '')) for img in soup.find_all('img') if 'src' in img.attrs]

        all_data.append({
            'url': url,
            'text': text,
            'images': images,
            'links': links,
        })

        for link in links:
            scrape_static(link)

    except Exception as e:
        print(f"Failed on {url}: {e}")

scrape_static(BASE_URL)
print(all_data)
