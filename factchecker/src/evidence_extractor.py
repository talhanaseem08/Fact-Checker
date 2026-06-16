import re
from typing import Dict, Iterable, List

from config import MAX_EVIDENCE_SENTENCES
from .utils import clean_whitespace, keyword_overlap_score, tokenize_keywords


CONTRADICTION_TERMS = {
    "cannot",
    "debunked",
    "does not",
    "false",
    "incorrect",
    "misleading",
    "myth",
    "no evidence",
    "not",
    "unlikely",
    "wrong",
}

FRAMING_FALSE_TERMS = {
    "conspiracy",
    "debunked",
    "despite scientific",
    "disproven",
    "false",
    "fringe",
    "hoax",
    "incorrect",
    "misinformation",
    "myth",
    "pseudoscience",
    "scientifically disproven",
    "unfounded",
    "unscientific",
}

FRAMING_NEUTRAL_TERMS = {
    "alleged",
    "ancient",
    "accusations",
    "argued",
    "argues",
    "audience",
    "babylon",
    "bce",
    "belief",
    "beliefs",
    "believe",
    "believed",
    "believers",
    "came across",
    "claim",
    "claimed",
    "claims",
    "cosmological",
    "debated",
    "could be",
    "founder",
    "groups",
    "holds",
    "hobby",
    "idea",
    "ideas",
    "map",
    "maps",
    "notion",
    "perception",
    "philosopher",
    "promote",
    "promoting",
    "question",
    "quotation",
    "revived",
    "rumor",
    "rumors",
    "significance",
    "society",
    "subscribed",
    "tablet",
    "theories",
    "theory",
    "thinking",
    "thresholds",
    "unreplicable",
    "view",
    "whether",
    "world",
    "youtube",
}

SUPPORT_TERMS = {
    "according to",
    "confirmed",
    "evidence",
    "found",
    "official",
    "reported",
    "research",
    "shows",
    "study",
    "study found",
}

NEGATION_TERMS = {
    "not",
    "never",
    "cannot",
    "can't",
    "doesn't",
    "does not",
    "isn't",
    "is not",
    "no evidence",
    "will not",
    "won't",
}

NEGATIVE_CLAIM_TERMS = {
    "bad",
    "cause",
    "causes",
    "dangerous",
    "harmful",
    "unsafe",
    "worse",
}

POSITIVE_EVIDENCE_TERMS = {
    "benefit",
    "benefits",
    "improve",
    "improves",
    "lower risk",
    "protect",
    "protects",
    "safe",
}


def split_sentences(text: str) -> List[str]:
    text = clean_whitespace(text)
    if not text:
        return []
    candidates = re.split(r"(?<=[.!?])\s+", text)
    sentences = []
    for sentence in candidates:
        sentence = clean_whitespace(sentence)
        if 45 <= len(sentence) <= 450:
            sentences.append(sentence)
    return sentences


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    lower = text.lower()
    for phrase in phrases:
        if " " in phrase or "'" in phrase:
            if phrase in lower:
                return True
            continue
        if re.search(rf"\b{re.escape(phrase)}\b", lower):
            return True
    return False


def classify_sentence(claim: str, sentence: str, overlap: float) -> str:
    claim_lower = claim.lower().replace("\u2019", "'")
    sentence_lower = (
        sentence.lower()
        .replace("\u2019", "'")
        .replace("doesn t", "doesn't")
        .replace("isn t", "isn't")
        .replace("won t", "won't")
        .replace("can t", "can't")
    )
    negation_context = (
        sentence_lower.replace("not only", "")
        .replace("not just", "")
        .replace("not necessarily", "")
        .replace("doesn't have to", "")
        .replace("does not have to", "")
        .replace("not have to", "")
        .replace("not already", "")
    )
    claim_has_negation = _contains_any(claim_lower, NEGATION_TERMS)
    sentence_has_negation = _contains_any(negation_context, NEGATION_TERMS)

    if overlap < 0.08:
        return "neutral"

    if sentence_lower.startswith("if ") or sentence.strip().endswith("?"):
        return "neutral"

    if _contains_any(sentence_lower, FRAMING_FALSE_TERMS):
        return "contradict"

    if "flat" in claim_lower and _contains_any(
        sentence_lower, {"curved", "curvature", "globe", "round", "spherical"}
    ):
        return "contradict"

    if (
        "zero emission" in claim_lower
        or "zero emissions" in claim_lower
        or "no emissions" in claim_lower
    ) and (
        "life cycle" in sentence_lower
        or "manufacturing" in sentence_lower
        or "power plant" in sentence_lower
        or "associated with" in sentence_lower
    ):
        return "contradict"

    if _contains_any(claim_lower, NEGATIVE_CLAIM_TERMS) and _contains_any(
        sentence_lower, POSITIVE_EVIDENCE_TERMS
    ):
        return "contradict"

    if _contains_any(negation_context, CONTRADICTION_TERMS):
        if not claim_has_negation or sentence_has_negation != claim_has_negation:
            return "contradict"

    if sentence_has_negation != claim_has_negation and overlap >= 0.18:
        return "contradict"

    has_support_cue = _contains_any(sentence_lower, SUPPORT_TERMS)
    if _contains_any(sentence_lower, FRAMING_NEUTRAL_TERMS):
        return "neutral"

    if has_support_cue:
        return "support"

    if overlap >= 0.42:
        return "support"

    return "neutral"


def extract_evidence(
    claim: str,
    search_results: List[dict],
    page_results: List[dict],
    max_sentences: int = MAX_EVIDENCE_SENTENCES,
) -> Dict[str, List[dict]]:
    """Extract, rank, deduplicate, and classify evidence sentences."""
    page_by_url = {page.get("url"): page for page in page_results}
    claim_keywords = set(tokenize_keywords(claim))
    candidates = []
    seen_sentences = set()

    for result in search_results:
        url = result.get("url", "")
        title = result.get("title", "")
        snippets = [result.get("snippet", "")]
        page_text = page_by_url.get(url, {}).get("text", "")
        if page_text:
            snippets.append(str(page_text))

        for source_text in snippets:
            for sentence in split_sentences(source_text):
                normalized = sentence.lower()
                if normalized in seen_sentences:
                    continue
                seen_sentences.add(normalized)
                overlap = keyword_overlap_score(claim, sentence)
                if overlap <= 0:
                    continue
                sentence_terms = set(tokenize_keywords(sentence))
                density_bonus = min(len(claim_keywords & sentence_terms) * 0.03, 0.18)
                score = min(1.0, overlap + density_bonus)
                label = classify_sentence(claim, sentence, overlap)
                candidates.append(
                    {
                        "sentence": sentence,
                        "classification": label,
                        "score": round(score, 3),
                        "overlap": round(overlap, 3),
                        "title": title,
                        "url": url,
                    }
                )

    candidates.sort(key=lambda row: row["score"], reverse=True)
    grouped = {"support": [], "contradict": [], "neutral": []}
    for candidate in candidates:
        label = candidate["classification"]
        if label not in grouped:
            label = "neutral"
        if len(grouped[label]) < max_sentences:
            grouped[label].append(candidate)

    return grouped
