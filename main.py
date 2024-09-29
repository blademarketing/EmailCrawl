import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

class AsyncEmailScraper:
    def __init__(self, max_depth, max_pages):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.extracted_urls = set()
        self.found_emails = set()
        self.pages_crawled = 0

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
                        if full_url not in self.extracted_urls:
                            self.extracted_urls.add(full_url)
                            tasks.append(self.crawl(session, full_url, depth + 1))

                    await asyncio.gather(*tasks)

        except Exception as e:
            print(f"Error fetching {url}: {e}")

    def extract_emails(self, html):
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, html)
        for email in emails:
            self.found_emails.add(email)

    async def start_crawling(self, start_url):
        async with aiohttp.ClientSession() as session:
            self.extracted_urls.add(start_url)
            await self.crawl(session, start_url, 0)

    def export_results(self):
        with open('found_emails.txt', 'w') as f:
            for email in self.found_emails:
                f.write(email + '\n')
        with open('extracted_urls.txt', 'w') as f:
            for url in self.extracted_urls:
                f.write(url + '\n')

if __name__ == "__main__":
    start_url = input("Enter the starting URL: ")
    max_depth = int(input("Enter the maximum depth to crawl: "))
    max_pages = int(input("Enter the maximum number of pages to crawl: "))

    scraper = AsyncEmailScraper(max_depth, max_pages)
    asyncio.run(scraper.start_crawling(start_url))
    scraper.export_results()
