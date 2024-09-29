import aiohttp
import asyncio
from aiohttp import web
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

class AsyncEmailScraper:
    def __init__(self, max_depth, max_pages, root_domain):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.root_domain = root_domain
        self.extracted_urls = set()
        self.found_emails = set()
        self.pages_crawled = 0

        # Define known file extensions to filter out
        self.known_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', 
                                 '.bmp', '.webp', '.ico', '.pdf', '.mp4', 
                                 '.avi', '.mov', '.wmv', '.mp3', '.wav', 
                                 '.zip', '.rar', '.tar', '.gz', '.js', 
                                 '.css', '.html']

    async def crawl(self, session, url, depth):
        # Return if depth exceeds max depth or if max pages have been crawled
        if depth > self.max_depth or self.pages_crawled >= self.max_pages:
            return

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    self.pages_crawled += 1
                    print(f"Crawled: {url}")
                    html = await response.text()
                    self.extract_emails(html)
                    soup = BeautifulSoup(html, 'html.parser')
                    links = soup.find_all('a', href=True)

                    tasks = []
                    for link in links:
                        href = link['href']
                        full_url = urljoin(url, href)

                        # Only queue new crawl tasks if we haven't reached the max pages yet
                        if self.pages_crawled < self.max_pages and self.is_internal_link(full_url):
                            if full_url not in self.extracted_urls:
                                self.extracted_urls.add(full_url)
                                tasks.append(self.crawl(session, full_url, depth + 1))

                    await asyncio.gather(*tasks)

        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")

    def extract_emails(self, html):
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, html)
        for email in emails:
            # Filter out emails with known extensions
            if not any(email.endswith(ext) for ext in self.known_extensions):
                self.found_emails.add(email)

    def is_internal_link(self, url):
        parsed_url = urlparse(url)
        return parsed_url.netloc == self.root_domain

    async def start_crawling(self, start_url):
        async with aiohttp.ClientSession() as session:
            self.extracted_urls.add(start_url)
            await self.crawl(session, start_url, 0)

async def handle_post(request):
    data = await request.json()
    start_url = data.get('url')
    max_depth = data.get('depth', 3)
    max_pages = data.get('max_pages', 50)
    
    # Format the URL
    if not start_url.startswith(("http://", "https://")):
        if start_url.startswith("www."):
            start_url = "http://" + start_url
        else:
            start_url = "http://www." + start_url

    root_domain = urlparse(start_url).netloc  # Get the root domain
    scraper = AsyncEmailScraper(max_depth, max_pages, root_domain)

    await scraper.start_crawling(start_url)

    # Return the emails found as JSON
    return web.json_response({'emails': list(scraper.found_emails)})

app = web.Application()
app.router.add_post('/scrape', handle_post)

if __name__ == "__main__":
    web.run_app(app, port=6662)
