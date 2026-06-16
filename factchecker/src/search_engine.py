import base64
import warnings
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
from bs4 import BeautifulSoup

from config import MAX_SEARCH_RESULTS, REQUEST_TIMEOUT
from .utils import clean_whitespace, is_valid_http_url, unique_by_url


def _normalize_result(title: str, url: str, snippet: str) -> Optional[dict]:
    title = clean_whitespace(title)
    url = (url or "").strip()
    snippet = clean_whitespace(snippet)
    if not title or not is_valid_http_url(url):
        return None
    return {"title": title, "url": url, "snippet": snippet}


def _search_with_ddgs(query: str, max_results: int) -> Tuple[List[dict], Optional[str]]:
    try:
        try:
            from ddgs import DDGS  # type: ignore
        except ImportError:
            from duckduckgo_search import DDGS

        rows = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            with DDGS() as ddgs:
                search_kwargs = {
                    "region": "wt-wt",
                    "safesearch": "moderate",
                    "max_results": max_results,
                }
                try:
                    search_items = ddgs.text(query, **search_kwargs)
                except TypeError:
                    search_items = ddgs.text(keywords=query, **search_kwargs)

                for item in search_items:
                    result = _normalize_result(
                        item.get("title", ""),
                        item.get("href") or item.get("url") or "",
                        item.get("body") or item.get("snippet") or "",
                    )
                    if result:
                        rows.append(result)
        return unique_by_url(rows)[:max_results], None
    except Exception as exc:
        return [], f"DuckDuckGo package search failed: {exc}"


def _search_with_html_fallback(query: str, max_results: int) -> Tuple[List[dict], Optional[str]]:
    try:
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0 Safari/537.36"
                )
            },
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows = []
        for result in soup.select(".result"):
            link = result.select_one(".result__a")
            snippet_el = result.select_one(".result__snippet")
            if not link:
                continue
            normalized = _normalize_result(
                link.get_text(" ", strip=True),
                link.get("href", ""),
                snippet_el.get_text(" ", strip=True) if snippet_el else "",
            )
            if normalized:
                rows.append(normalized)
            if len(rows) >= max_results:
                break
        return unique_by_url(rows)[:max_results], None
    except Exception as exc:
        return [], f"DuckDuckGo HTML fallback failed: {exc}"


def _decode_bing_url(url: str) -> str:
    parsed = urlparse(url)
    if "bing.com" not in parsed.netloc or "/ck/" not in parsed.path:
        return url

    encoded = parse_qs(parsed.query).get("u", [""])[0]
    if not encoded:
        return url
    if encoded.startswith("a1"):
        encoded = encoded[2:]

    padding = "=" * (-len(encoded) % 4)
    try:
        return base64.urlsafe_b64decode(encoded + padding).decode("utf-8")
    except Exception:
        return unquote(encoded)


def _search_with_bing_fallback(query: str, max_results: int) -> Tuple[List[dict], Optional[str]]:
    try:
        url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0 Safari/537.36"
                )
            },
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows = []
        for result in soup.select("li.b_algo"):
            link = result.select_one("h2 a")
            snippet_el = result.select_one("p")
            if not link:
                continue
            normalized = _normalize_result(
                link.get_text(" ", strip=True),
                _decode_bing_url(link.get("href", "")),
                snippet_el.get_text(" ", strip=True) if snippet_el else "",
            )
            if normalized:
                rows.append(normalized)
            if len(rows) >= max_results:
                break
        return unique_by_url(rows)[:max_results], None
    except Exception as exc:
        return [], f"Bing HTML fallback failed: {exc}"


def search_web(
    query: str, max_results: int = MAX_SEARCH_RESULTS
) -> Tuple[List[dict], Optional[str]]:
    """Search DuckDuckGo without an API key and return normalized results."""
    query = clean_whitespace(query)
    if not query:
        return [], "Search query is empty."

    results, error = _search_with_ddgs(query, max_results)
    if results:
        return results, error

    fallback_results, fallback_error = _search_with_html_fallback(query, max_results)
    if fallback_results:
        if error:
            return fallback_results, error
        return fallback_results, None

    bing_results, bing_error = _search_with_bing_fallback(query, max_results)
    if bing_results:
        nonfatal_errors = "; ".join(message for message in [error, fallback_error] if message)
        if nonfatal_errors:
            return bing_results, nonfatal_errors
        return bing_results, None

    combined_error = "; ".join(
        message for message in [error, fallback_error, bing_error] if message
    )
    return [], combined_error or "Search returned no usable results."
