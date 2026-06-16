import re
from datetime import datetime
from typing import Iterable, List
from urllib.parse import urlparse


STOPWORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "doing",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "now",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
}


SENSITIVE_TERMS = {
    "advice",
    "attorney",
    "bankruptcy",
    "cancer",
    "cardiac",
    "contract",
    "court",
    "credit",
    "debt",
    "diagnosis",
    "disease",
    "doctor",
    "drug",
    "finance",
    "financial",
    "health",
    "insurance",
    "investment",
    "law",
    "lawsuit",
    "legal",
    "loan",
    "medical",
    "medicine",
    "mortgage",
    "prescription",
    "retirement",
    "stock",
    "surgery",
    "tax",
    "therapy",
    "treatment",
}


def clean_whitespace(text: str) -> str:
    """Normalize whitespace while preserving readable text."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize_keywords(text: str, min_length: int = 3) -> List[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9'-]*", (text or "").lower())
    return [
        token
        for token in tokens
        if len(token) >= min_length and token not in STOPWORDS
    ]


def keyword_overlap_score(claim: str, sentence: str) -> float:
    claim_terms = set(tokenize_keywords(claim))
    if not claim_terms:
        return 0.0
    sentence_terms = set(tokenize_keywords(sentence))
    if not sentence_terms:
        return 0.0
    return len(claim_terms & sentence_terms) / len(claim_terms)


def safe_domain(url: str) -> str:
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return ""
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def is_valid_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def unique_by_url(items: Iterable[dict]) -> List[dict]:
    seen = set()
    unique = []
    for item in items:
        url = (item.get("url") or "").strip()
        normalized = url.rstrip("/").lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(item)
    return unique


def current_timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def is_sensitive_claim(text: str) -> bool:
    terms = set(tokenize_keywords(text, min_length=3))
    return bool(terms & SENSITIVE_TERMS)


def is_context_limited_claim(text: str) -> bool:
    lower = f" {clean_whitespace(text).lower()} "
    markers = [
        " at my university ",
        " last week",
        " my ",
        " my neighbor",
        " this exact",
        " this morning",
        " unnamed",
        " unknown town",
        " yesterday",
    ]
    local_phrases = [
        "local chess club",
        "private startup",
        "on my desk",
        "overnight",
    ]
    return any(marker in lower for marker in markers) or any(
        phrase in lower for phrase in local_phrases
    )


def clamp(value: float, low: int = 0, high: int = 100) -> int:
    return int(max(low, min(high, round(value))))
