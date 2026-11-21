"""Collect listing metadata from the Quotes to Scrape practice site."""

import csv
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


START_URL = "https://quotes.toscrape.com/"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "HR.CSV"
REQUEST_DELAY_SECONDS = 1
REQUEST_TIMEOUT_SECONDS = 20


def scrape_page(url, session):
    response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    records = []

    for listing in soup.select("div.quote"):
        author = listing.select_one("small.author")
        author_link = listing.select_one("span a")
        tags = [tag.get_text(strip=True) for tag in listing.select(".tags a.tag")]

        if author is None:
            raise ValueError(f"Listing on {url} is missing its author")

        author_profile_url = (
            urljoin(url, author_link["href"])
            if author_link is not None and author_link.get("href")
            else ""
        )
        records.append(
            {
                "author": author.get_text(strip=True),
                "tags": "; ".join(tags),
                "tag_count": len(tags),
                "author_profile_url": author_profile_url,
                "source_page_url": url,
            }
        )

    next_link = soup.select_one("li.next a")
    next_url = (
        urljoin(url, next_link["href"])
        if next_link is not None and next_link.get("href")
        else None
    )
    return records, next_url


def scrape_all_pages():
    records = []
    visited_urls = set()
    url = START_URL

    with requests.Session() as session:
        session.headers.update(
            {"User-Agent": "HRListingPracticeScraper/1.0 (educational use)"}
        )

        while url and url not in visited_urls:
            visited_urls.add(url)
            page_records, next_url = scrape_page(url, session)
            if not page_records:
                break

            records.extend(page_records)
            url = next_url
            if url:
                time.sleep(REQUEST_DELAY_SECONDS)

    if not records:
        raise RuntimeError(f"No listing metadata was found at {START_URL}")
    return records


def main():
    records = scrape_all_pages()
    fieldnames = [
        "author",
        "tags",
        "tag_count",
        "author_profile_url",
        "source_page_url",
    ]

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Saved {len(records)} listings to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()