import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time

# Configuration
DOMAINS = [
    "https://www.jewelchangiairport.com/",
    "https://www.changiairport.com/",
]
OUTPUT_FILE = "scraped_data.jsonl"
MAX_PAGES_PER_DOMAIN = 100  # Reasonable limit to prevent infinite loops
MAX_TOTAL_PAGES = 200  # Total limit across all domains
CRAWL_DELAY = 2  # seconds between requests (increased to be more respectful)

# File extensions to skip
SKIP_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.css', '.js', '.xml', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}


def is_internal_link(link, base_netloc):
    parsed = urlparse(link)
    # Empty netloc means relative URL, treat as internal
    if not parsed.netloc:
        return True
    return parsed.netloc == base_netloc

def should_skip_url(url):
    """Check if URL should be skipped based on various criteria."""
    parsed = urlparse(url)
    
    # Skip file extensions we don't want
    path = parsed.path.lower()
    for ext in SKIP_EXTENSIONS:
        if path.endswith(ext):
            return True
    
    # Skip URLs with query parameters that might be dynamic content
    if parsed.query:
        # Skip URLs with common dynamic parameters
        skip_params = {'page', 'p', 'id', 'ref', 'utm_', 'fbclid', 'gclid'}
        if any(param in parsed.query.lower() for param in skip_params):
            return True
    
    # Skip URLs that are too deep (more than 4 path segments)
    path_segments = [seg for seg in parsed.path.split('/') if seg]
    if len(path_segments) > 4:
        return True
    
    # Skip URLs with fragments (anchor links)
    if parsed.fragment:
        return True
    
    return False


def get_links(soup, base_url):
    links = set()
    base_netloc = urlparse(base_url).netloc
    for a in soup.find_all("a", href=True):
        href = a["href"].split("#")[0]  # strip fragments
        full_url = urljoin(base_url, href)
        if is_internal_link(full_url, base_netloc) and not should_skip_url(full_url):
            links.add(full_url)
    return links


def extract_text(soup):
    # Extract text from title, headings, paragraphs
    texts = []
    if soup.title:
        texts.append(soup.title.get_text(strip=True))
    for tag in ["h1", "h2", "h3", "p"]:
        for el in soup.find_all(tag):
            txt = el.get_text(strip=True)
            if txt:
                texts.append(txt)
    return "\n".join(texts)


def scrape_site(base_url, total_scraped_count):
    visited = set()
    to_visit = {base_url}
    domain_data = []
    base_netloc = urlparse(base_url).netloc
    pages_scraped = 0

    print(f"Starting to scrape {base_url} (max {MAX_PAGES_PER_DOMAIN} pages)")

    while to_visit and pages_scraped < MAX_PAGES_PER_DOMAIN and total_scraped_count < MAX_TOTAL_PAGES:
        url = to_visit.pop()
        if url in visited:
            continue
            
        # Check if we've hit the total limit
        if total_scraped_count >= MAX_TOTAL_PAGES:
            print(f"Reached total page limit ({MAX_TOTAL_PAGES}), stopping...")
            break
            
        try:
            resp = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            resp.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            visited.add(url)  # Mark as visited to avoid retrying
            continue

        # Try different parsers if the default one fails
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            print(f"HTML parser failed for {url}, trying lxml: {e}")
            try:
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as e2:
                print(f"LXML parser also failed for {url}, trying html5lib: {e2}")
                try:
                    soup = BeautifulSoup(resp.text, "html5lib")
                except Exception as e3:
                    print(f"All parsers failed for {url}, skipping: {e3}")
                    visited.add(url)
                    continue
                    
        text = extract_text(soup)
        
        # Only add if we got meaningful content
        if text and len(text.strip()) > 50:  # Minimum content length
            domain_data.append({"url": url, "text": text})
            pages_scraped += 1
            total_scraped_count += 1
            print(f"Scraped ({pages_scraped}/{MAX_PAGES_PER_DOMAIN}) {url} - {len(text)} chars")
        else:
            print(f"Skipped {url} - insufficient content ({len(text) if text else 0} chars)")
            
        visited.add(url)  # Always mark as visited

        # Crawl new links (but limit how many we add to prevent infinite growth)
        new_links = get_links(soup, base_url)
        links_added = 0
        for link in new_links:
            if link not in visited and link not in to_visit and links_added < 10:  # Limit new links per page
                to_visit.add(link)
                links_added += 1

        time.sleep(CRAWL_DELAY)

    print(f"Completed scraping {base_url}: {pages_scraped} pages scraped")
    return domain_data, total_scraped_count


def main():
    total_scraped = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as fout:
        for domain in DOMAINS:
            if total_scraped >= MAX_TOTAL_PAGES:
                print(f"Reached total limit ({MAX_TOTAL_PAGES}), stopping scraping...")
                break
                
            print(f"Starting scrape for {domain}")
            pages, total_scraped = scrape_site(domain, total_scraped)
            for page in pages:
                fout.write(json.dumps(page, ensure_ascii=False) + "\n")
                
    print(f"Scraping completed. Total pages scraped: {total_scraped}. Data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
