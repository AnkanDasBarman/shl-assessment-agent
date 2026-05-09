import argparse
import json
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.shl.com"
CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"
SITEMAP_URL = "https://www.shl.com/sitemap.xml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

VIEW_PATH = "/products/product-catalog/view/"


class Scraper:
    def __init__(self, delay: float, timeout: int, max_retries: int) -> None:
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def get(self, url: str) -> requests.Response:
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                res = self.session.get(url, timeout=self.timeout)
                if res.status_code >= 400:
                    raise requests.HTTPError(f"HTTP {res.status_code}", response=res)
                return res
            except Exception as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    time.sleep(min(2.0 * attempt, 6.0))
        raise RuntimeError(f"Failed GET {url}: {last_exc}")


def text_or_empty(node) -> str:
    return node.get_text(" ", strip=True) if node else ""


def normalize_list_text(value: str) -> List[str]:
    if not value:
        return []
    cleaned = value.replace("\n", " ").strip().strip(",")
    if not cleaned:
        return []
    parts = [p.strip() for p in cleaned.split(",")]
    return [p for p in parts if p]


def extract_entity_id(url: str) -> Optional[str]:
    m = re.search(r"-(\d+)/?$", url)
    if m:
        return m.group(1)
    return None


def parse_kv_blocks(soup: BeautifulSoup) -> Dict[str, str]:
    out: Dict[str, str] = {}

    # Definition lists
    for dl in soup.find_all("dl"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        for dt, dd in zip(dts, dds):
            k = text_or_empty(dt).lower()
            v = text_or_empty(dd)
            if k and v:
                out[k] = v

    # Table rows
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if len(cells) >= 2:
            k = text_or_empty(cells[0]).lower()
            v = text_or_empty(cells[1])
            if k and v:
                out[k] = v

    return out


def pick_value(kv: Dict[str, str], keys: List[str]) -> str:
    for k, v in kv.items():
        if any(key in k for key in keys):
            return v
    return ""


def parse_detail(url: str, html: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")

    title = text_or_empty(soup.find("h1"))
    if not title:
        og_title = soup.find("meta", attrs={"property": "og:title"})
        title = (og_title.get("content", "") if og_title else "").strip()

    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = (meta_desc.get("content", "") if meta_desc else "").strip()

    kv = parse_kv_blocks(soup)

    duration = pick_value(kv, ["completion time", "duration"])
    job_levels_raw = pick_value(kv, ["job level", "job levels"])
    languages_raw = pick_value(kv, ["language", "languages"])
    remote_raw = pick_value(kv, ["remote"])
    adaptive_raw = pick_value(kv, ["adaptive"])

    # category tags fallback
    keys = []
    for node in soup.select("a,span,li"):
        txt = text_or_empty(node)
        if txt in {
            "Knowledge & Skills",
            "Simulations",
            "Ability & Aptitude",
            "Personality & Behavior",
            "Competencies",
            "Assessment Exercises",
            "Development & 360",
            "Biodata & Situational Judgment",
        } and txt not in keys:
            keys.append(txt)

    remote = ""
    if remote_raw:
        low = remote_raw.lower()
        if "yes" in low:
            remote = "yes"
        elif "no" in low:
            remote = "no"

    adaptive = ""
    if adaptive_raw:
        low = adaptive_raw.lower()
        if "yes" in low:
            adaptive = "yes"
        elif "no" in low:
            adaptive = "no"

    now = datetime.now(timezone.utc).isoformat()

    return {
        "entity_id": extract_entity_id(url) or "",
        "name": title,
        "link": url,
        "scraped_at": now,
        "job_levels": normalize_list_text(job_levels_raw),
        "job_levels_raw": job_levels_raw,
        "languages": normalize_list_text(languages_raw),
        "languages_raw": languages_raw,
        "duration": duration,
        "duration_raw": duration,
        "status": "ok",
        "remote": remote,
        "adaptive": adaptive,
        "description": description,
        "keys": keys,
    }


def extract_links_from_html(html: str) -> Set[str]:
    soup = BeautifulSoup(html, "lxml")
    urls: Set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full = urljoin(BASE_URL, href)
        if VIEW_PATH in full:
            urls.add(full.split("?")[0].rstrip("/" ) + "/")

    return urls


def collect_links(scraper: Scraper, max_pages: int = 40) -> List[str]:
    links: Set[str] = set()

    # Strategy 1: catalog page variants
    page_urls = [CATALOG_URL]
    for p in range(2, max_pages + 1):
        page_urls.append(f"{CATALOG_URL}?page={p}")

    for u in page_urls:
        try:
            res = scraper.get(u)
            found = extract_links_from_html(res.text)
            if not found and u != CATALOG_URL:
                break
            links.update(found)
            time.sleep(scraper.delay)
        except Exception:
            if u == CATALOG_URL:
                pass
            continue

    # Strategy 2: sitemap
    try:
        res = scraper.get(SITEMAP_URL)
        soup = BeautifulSoup(res.text, "xml")
        for loc in soup.find_all("loc"):
            url = (loc.get_text() or "").strip()
            if VIEW_PATH in url:
                links.add(url.split("?")[0].rstrip("/") + "/")
    except Exception:
        pass

    return sorted(links)


def run(output: str, delay: float, timeout: int, max_retries: int) -> None:
    scraper = Scraper(delay=delay, timeout=timeout, max_retries=max_retries)
    links = collect_links(scraper)

    print(f"Discovered {len(links)} assessment links")
    if not links:
        raise RuntimeError(
            "Discovered 0 links. Aborting without overwriting existing raw dataset."
        )

    rows: List[Dict] = []

    for i, link in enumerate(links, start=1):
        print(f"[{i}/{len(links)}] Scraping {link}")
        try:
            res = scraper.get(link)
            item = parse_detail(link, res.text)
        except Exception as exc:
            item = {
                "entity_id": extract_entity_id(link) or "",
                "name": "",
                "link": link,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "job_levels": [],
                "job_levels_raw": "",
                "languages": [],
                "languages_raw": "",
                "duration": "",
                "duration_raw": "",
                "status": f"error: {exc}",
                "remote": "",
                "adaptive": "",
                "description": "",
                "keys": [],
            }
        rows.append(item)
        time.sleep(delay)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(rows)} records -> {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape SHL product catalog details.")
    parser.add_argument("--output", default="data/raw/shl_catalog.json")
    parser.add_argument("--delay", type=float, default=0.8)
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()

    run(
        output=args.output,
        delay=args.delay,
        timeout=args.timeout,
        max_retries=args.max_retries,
    )


if __name__ == "__main__":
    main()
