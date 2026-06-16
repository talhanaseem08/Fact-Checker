from typing import Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import MAX_CHARS_PER_PAGE, REQUEST_TIMEOUT
from .utils import clean_whitespace


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0 Safari/537.36"
)

BINARY_EXTENSIONS = {
    ".7z",
    ".avi",
    ".bin",
    ".doc",
    ".docx",
    ".gif",
    ".gz",
    ".jpg",
    ".jpeg",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".ppt",
    ".pptx",
    ".rar",
    ".tar",
    ".webp",
    ".xls",
    ".xlsx",
    ".zip",
}


def _has_binary_extension(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in BINARY_EXTENSIONS)


def _extract_with_trafilatura(html: str, url: str) -> str:
    try:
        import trafilatura

        extracted = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=False,
            favor_recall=True,
        )
        return clean_whitespace(extracted or "")
    except Exception:
        return ""


def _extract_with_bs4(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form"]):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    if not paragraphs:
        paragraphs = [soup.get_text(" ", strip=True)]
    return clean_whitespace(" ".join(paragraphs)), clean_whitespace(title)


def read_url(url: str, max_chars: int = MAX_CHARS_PER_PAGE) -> Dict[str, object]:
    """Fetch and extract readable text from a webpage."""
    result: Dict[str, object] = {
        "url": url,
        "title": "",
        "text": "",
        "success": False,
        "error": None,
    }

    if _has_binary_extension(url):
        result["error"] = "Skipped binary or document URL."
        return result

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if "pdf" in content_type or (
            "text/html" not in content_type and "application/xhtml" not in content_type
        ):
            result["error"] = f"Skipped unsupported content type: {content_type or 'unknown'}"
            return result

        html = response.text
        text = _extract_with_trafilatura(html, url)
        bs4_text, title = _extract_with_bs4(html)
        if not text:
            text = bs4_text
        if not title:
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.get_text(" ", strip=True) if soup.title else ""

        result.update(
            {
                "title": title,
                "text": clean_whitespace(text)[:max_chars],
                "success": bool(text),
                "error": None if text else "No readable text extracted.",
            }
        )
        return result
    except Exception as exc:
        result["error"] = str(exc)
        return result

