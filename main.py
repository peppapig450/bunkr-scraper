import argparse
from pprint import pprint

from src.bunkr_scraper import BunkrScraper


def main():
    parser = argparse.ArgumentParser(description="Bunkr Scraper")
    parser.add_argument("search_term", type=str, help="Search term for Bunkr")
    args = parser.parse_args()

    scraper = BunkrScraper(args.search_term)
    results = scraper.run_scraper()
    pprint(results)


if __name__ == "__main__":
    main()
