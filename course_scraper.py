import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time
import random
import html
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    )
}


def _safe_get(url, timeout=15):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def page_indicates_free(html_text: str) -> bool:
    if not html_text:
        return False
    t = html_text.lower()
    # quick textual hints
    if "100% off" in t or "free course" in t or "enroll for free" in t or "audit" in t:
        return True

    # JSON-like patterns used by Udemy/Coursera/others: isPaid / is_paid / amount:0
    if re.search(r'"isPaid"\s*:\s*false', t) or re.search(r'"is_paid"\s*:\s*false', t):
        return True

    if re.search(r'"amount"\s*:\s*0\b', t) or re.search(r'"price"\s*:\s*\{[^}]*"amount"\s*:\s*0', t):
        return True

    # dollar zero or $0
    if "$0" in t or "£0" in t or "€0" in t:
        return True

    # fallback: presence of the word 'free' near price-related words
    if re.search(r'(price|cost|paid|discount).{0,80}free', t):
        return True

    return False


def _extract_udemy(soup, base_url):
    found = []
    # Look for links that look like course pages
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/course/" in href:
            title = a.get_text(strip=True)
            if not title:
                # try nested tags
                title = a.find("div") and a.find("div").get_text(strip=True) or ""

            link = urljoin(base_url, href)

            # try to find rating nearby
            rating = None
            parent = a.parent
            rating_tag = parent.find("span", attrs={"data-purpose": "rating-number"}) if parent else None
            if rating_tag:
                try:
                    rating = float(rating_tag.get_text(strip=True))
                except Exception:
                    rating = None

            # determine if this course is free (0 cost / 100% off)
            is_free = False

            def _text_has_free(txt):
                if not txt:
                    return False
                t = txt.lower()
                return (
                    "100% off" in t
                    or "free" in t
                    or "$0" in t
                    or "0.00" in t
                    or "free course" in t
                    or "enroll for free" in t
                )

            # check the anchor and nearby nodes for free indicators
            if _text_has_free(a.get_text(" ")):
                is_free = True
            elif parent and _text_has_free(parent.get_text(" ")):
                is_free = True
            else:
                # look a bit higher in DOM and also search for price-like tokens
                ancestor = parent
                for _ in range(4):
                    if not ancestor:
                        break
                    txt = ancestor.get_text(" ")
                    if _text_has_free(txt) or re.search(r"\$\s*0|100%\s*off|free", txt, re.IGNORECASE):
                        is_free = True
                        break
                    ancestor = ancestor.parent

            # if still unsure, fetch the course page and inspect with stronger heuristics
            if not is_free:
                page = _safe_get(link, timeout=10)
                if page:
                    try:
                        if page_indicates_free(page):
                            is_free = True
                    except Exception:
                        is_free = False

            # only include when course is confirmed free and rating condition holds
            if is_free and (rating is None or rating >= 4.0):
                found.append({"platform": "Udemy", "title": html.escape(title), "link": link})

    return found


def _extract_coursera(soup, base_url):
    found = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/learn/") or "/professional-certificates/" in href or "/specializations/" in href:
            title = a.get_text(strip=True)
            link = urljoin(base_url, href)

            # Coursera often does not show rating on search; accept if rating missing
            rating = None
            # try to find rating in nearby nodes
            parent = a.parent
            if parent:
                r = parent.find("span", class_="ratings-text")
                if r:
                    try:
                        rating = float(r.get_text(strip=True).split()[0])
                    except Exception:
                        rating = None

            # ensure it's free (look for free/audit indicators)
            def _has_free_text(node):
                if not node:
                    return False
                t = node.get_text(" ").lower()
                return (
                    "free" in t
                    or "audit" in t
                    or "enroll for free" in t
                    or "100% off" in t
                    or "$0" in t
                )

            is_free = False
            if _has_free_text(a):
                is_free = True
            elif parent and _has_free_text(parent):
                is_free = True
            else:
                ancestor = parent
                for _ in range(4):
                    if not ancestor:
                        break
                    txt = ancestor.get_text(" ")
                    if _has_free_text(ancestor) or re.search(r"\$\s*0|100%\s*off|free", txt, re.IGNORECASE):
                        is_free = True
                        break
                    ancestor = ancestor.parent

            if not is_free:
                page = _safe_get(link, timeout=10)
                if page:
                    try:
                        if page_indicates_free(page):
                            is_free = True
                    except Exception:
                        is_free = False

            if is_free and (rating is None or rating >= 4.0):
                found.append({"platform": "Coursera", "title": html.escape(title), "link": link})

    return found


def _extract_udacity(soup, base_url):
    found = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/course/" in href:
            title = a.get_text(strip=True)
            link = urljoin(base_url, href)
            # Udacity catalog entries sometimes include "Free" badge; we can't always detect reliably here
            def _has_free_text(node):
                if not node:
                    return False
                t = node.get_text(" ").lower()
                return ("free" in t or "100% off" in t or "$0" in t)

            is_free = False
            if _has_free_text(a):
                is_free = True
            elif a.parent and _has_free_text(a.parent):
                is_free = True
            else:
                page = _safe_get(link, timeout=10)
                if page:
                    try:
                        if page_indicates_free(page):
                            is_free = True
                    except Exception:
                        is_free = False

            if is_free:
                found.append({"platform": "Udacity", "title": html.escape(title), "link": link})
    return found


def scrape_url(url):
    html_text = _safe_get(url)
    if not html_text:
        return []

    soup = BeautifulSoup(html_text, "html.parser")
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    base = f"{parsed.scheme}://{parsed.netloc}"

    # Select extractor based on domain
    if "udemy.com" in domain:
        return _extract_udemy(soup, base)
    if "coursera.org" in domain:
        return _extract_coursera(soup, base)
    if "udacity.com" in domain:
        return _extract_udacity(soup, base)

    # Generic fallback: find links that look like course pages
    results = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)
        if not title:
            continue
        if any(k in href for k in ["/course/", "/learn/", "/specializations/"]):
            link = urljoin(base, href)
            results.append({"platform": parsed.netloc, "title": html.escape(title), "link": link})

    return results


def scrape_urls(urls):
    all_found = []
    for url in urls:
        # polite random small delay to avoid hammering
        time.sleep(0.5 + random.random() * 0.8)
        try:
            scraped = scrape_url(url)
            if scraped:
                all_found.extend(scraped)
        except Exception:
            # continue on error
            continue

    # deduplicate by link while preserving first-seen order
    seen = set()
    deduped = []
    for c in all_found:
        if c["link"] not in seen:
            seen.add(c["link"])
            deduped.append(c)

    return deduped
