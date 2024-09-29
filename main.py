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

                        # Check if we should stop crawling based on page limits
                        if self.pages_crawled < self.max_pages and self.is_internal_link(full_url):
                            if full_url not in self.extracted_urls:
                                self.extracted_urls.add(full_url)
                                tasks.append(self.crawl(session, full_url, depth + 1))

                    await asyncio.gather(*tasks)

        except Exception as e:
            print(f"Error fetching {url}: {str(e
