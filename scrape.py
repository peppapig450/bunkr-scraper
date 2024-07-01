import requests
from urllib.parse import urlparse, urlencode, urlunparse
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import re
from itertools import chain


class BunkrScrapingError(Exception):
    pass


type results_dict = dict[str, dict[str, int | str]]


class BunkrScraper:
    def __init__(self, search_term: str) -> None:
        self.base_url = "https://bunkr-albums.io/"
        self.search_url = self.create_url(search_term)
        self.links: list[str] = []
        self.results: results_dict = {}

        # Compiled regex patterns
        self.file_count_pattern = re.compile(r"(\d+) files")
        self.size_pattern = re.compile(r"(\d+(\.d+)?) (KB|MB|GB|TB)")

    def create_url(self, search_term: str):
        base_url = "https://bunkr-albums.io/"

        # parse the base url
        parsed_url = urlparse(base_url)

        # construct the search query string
        query = {"search": search_term}

        # Combine URL parts and query string
        search_url = urlunparse(
            (
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                urlencode(query),
                parsed_url.fragment,
            )
        )
        return search_url

    def make_search_request(self, search_url: str):
        try:
            response = requests.get(search_url)
            response.raise_for_status()

            # Access the HTML if the request is successful
            html_content = response.text
            return html_content

        except requests.exceptions.RequestException as e:
            raise BunkrScrapingError(
                f"Something went wrong making the request for the url {search_url}"
            ) from e

    def scrape_bunkr_links(self, html_content: str):
        soup = BeautifulSoup(html_content, "lxml")
        bunkr_links = soup.select("tr > td > a[href]")
        self.links = list(
            chain.from_iterable(
                link["href"] for link in bunkr_links if isinstance(link["href"], str)
            )
        )

    async def fetch_link_html(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()

    async def scrape_data_from_link(self, url: str):
        link_html = await self.fetch_link_html(url)
        soup = BeautifulSoup(link_html, "lxml")

        # Find the span element containing files and size information
        span = soup.select_one("span.text-[16px].break-normal")

        if span:
            span_text = span.get_text(strip=True)
            file_count_match = self.file_count_pattern.search(span_text)
            size_match = self.size_pattern.search(span_text)

            file_count = int(file_count_match.group(1)) if file_count_match else 0
            size = size_match.group(0) if size_match else "0 KB"

            self.results[url] = {"files": file_count, "size": size}
        else:
            self.results[url] = {"files": 0, "size": "Error"}

    async def scrape_data_from_links(self):
        async with asyncio.TaskGroup() as group:
            for link in self.links:
                await group.create_task(self.scrape_data_from_link(link), name=link)

    def run_scraper(self):
        html = self.make_search_request(self.search_url)
        self.scrape_bunkr_links(html)

        asyncio.run(self.scrape_data_from_links())

        return self.results


if __name__ == "__main__":
    search = input("Enter search term for bunkr: ")
    url = create_url(search)
    html = make_search_request(url)
    links = scrape_bunkr_links(html)
    print(links)
