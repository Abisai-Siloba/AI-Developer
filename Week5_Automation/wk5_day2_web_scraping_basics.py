# 1. install the required libraries; pip install requests beautifulsoup4 and test using books.toscrape.com

import requests
from bs4 import BeautifulSoup

response = requests.get("https://books.toscrape.com/")
print("Status:", response.status_code)
print("Page size:", len(response.text), "characters")
print()

# 2. parse the HTML content using BeautifulSoup and print the title of the page
soup = BeautifulSoup(response.text, "html.parser")
print("Title:", soup.title.text)
print()

# 3. find all the book articles on the page and print them with their prices
books = soup.find_all("article", class_="product_pod")
print("Books found:", len(books), "books on the page")
for book in books:
    title = book.find("h3").a["title"]
    price = book.find("p", class_="price_color").text
    print(f"Book Title: {title}, Price: {price}")
print()

# 4. save the scraped data to a CSV file
import csv

book_data = []
for book in books:
    title = book.find("h3").a["title"]
    price = book.find("p", class_="price_color").text
    rating = book.find("p", class_="star-rating")["class"][1]
    book_data.append(["Title", title, "Price", price, "Rating", rating])

with open("books.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Title", "Price", "Rating"])
    for book in book_data:
        writer.writerow([book[1], book[3], book[5]])
print(f"Saved {len(book_data)} books to books.csv")


# 5. Handle errors that happen when scraping. Websites change their HTML, servers go down, and your connection drops. Protect your script:
import time

def fetch_page(url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            return response
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("All attempts failed. Exiting.")
                return None