import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree


HOST = "127.0.0.1"
PORT = 8000
PAGE = Path(__file__).with_name("wk1_day5_project.html")
TOPICS = {
    "technology": "TECHNOLOGY",
    "business": "BUSINESS",
    "health": "HEALTH",
    "sports": "SPORTS",
}
EDITIONS = {
    "us": ("en-US", "US", "US:en"),
    "gb": ("en-GB", "GB", "GB:en"),
    "ca": ("en-CA", "CA", "CA:en"),
    "au": ("en-AU", "AU", "AU:en"),
    "in": ("en-IN", "IN", "IN:en"),
}


def read_headlines(category: str, country: str) -> list[dict[str, str]]:
    hl, gl, ceid = EDITIONS[country]
    query = urlencode({"hl": hl, "gl": gl, "ceid": ceid})
    feed_url = (
        f"https://news.google.com/rss/headlines/section/topic/{TOPICS[category]}?{query}"
    )
    request = Request(
        feed_url,
        headers={"User-Agent": "DailyBrief/1.0 (RSS reader)"},
    )

    with urlopen(request, timeout=15) as response:
        feed = ElementTree.fromstring(response.read())

    articles = []
    for item in feed.findall("./channel/item"):
        full_title = item.findtext("title", default="").strip()
        title, separator, source = full_title.rpartition(" - ")
        articles.append(
            {
                "title": title if separator else full_title,
                "source": source if separator else "Google News",
                "publishedAt": item.findtext("pubDate", default="").strip(),
                "url": item.findtext("link", default="").strip(),
            }
        )
    return articles


class NewsBriefHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/":
            self._send_page()
            return
        if parsed_url.path != "/api/headlines":
            self.send_error(404, "Not found")
            return

        params = parse_qs(parsed_url.query)
        category = params.get("category", [""])[0]
        country = params.get("country", [""])[0]
        if category not in TOPICS or country not in EDITIONS:
            self._send_json(
                {"error": "Choose a supported topic and edition."},
                status=400,
            )
            return

        try:
            articles = read_headlines(category, country)
        except (HTTPError, URLError, TimeoutError, ElementTree.ParseError) as error:
            if isinstance(error, HTTPError):
                message = f"Google News returned HTTP {error.code}."
            elif isinstance(error, ElementTree.ParseError):
                message = "Google News returned an invalid RSS feed."
            else:
                message = "Could not reach Google News. Check your connection and try again."
            self._send_json({"error": message}, status=502)
            return

        self._send_json({"articles": articles})

    def _send_page(self) -> None:
        try:
            content = PAGE.read_bytes()
        except OSError:
            self.send_error(500, "Could not read the news brief page.")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, data: dict[str, object], status: int = 200) -> None:
        content = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), NewsBriefHandler)
    print(f"Daily Brief is running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Daily Brief.")
    finally:
        server.server_close()
