from typing import Dict, List, Optional

from config import MAX_PAGES_TO_READ
from .evidence_extractor import extract_evidence
from .llm_utils import fallback_answer, generate_grounded_answer
from .scoring import calculate_confidence
from .search_engine import search_web
from .utils import (
    clean_whitespace,
    current_timestamp,
    is_context_limited_claim,
    is_sensitive_claim,
    safe_domain,
)
from .web_reader import read_url


def _empty_result(claim: str, message: str) -> dict:
    return {
        "claim": claim,
        "verdict": "Insufficient Evidence",
        "answer": message,
        "confidence": 5,
        "confidence_label": "Low",
        "supporting_evidence": [],
        "contradicting_evidence": [],
        "neutral_evidence": [],
        "sources": [],
        "warnings": [message],
        "timestamp": current_timestamp(),
        "search_error": message,
    }


def _build_sources(search_results: List[dict]) -> List[dict]:
    sources = []
    seen = set()
    for result in search_results:
        url = result.get("url", "")
        normalized = url.rstrip("/").lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        sources.append(
            {
                "title": result.get("title", "Untitled"),
                "url": url,
                "snippet": result.get("snippet", ""),
                "domain": safe_domain(url),
            }
        )
    return sources


def _is_absolute_claim(claim: str) -> bool:
    absolute_terms = [
        "all",
        "always",
        "completely",
        "everyone",
        "everybody",
        "never",
        "necessary for everyone",
        "only",
        "zero",
    ]
    claim_lower = claim.lower()
    return any(term in claim_lower for term in absolute_terms)


def _strong_contradiction_count(items: List[dict]) -> int:
    strong_terms = [
        "conspiracy",
        "curvature",
        "debunked",
        "disproven",
        "doesn't",
        "does not",
        "false",
        "is not",
        "isn't",
        "mistaken",
        "myth",
        "no evidence",
        "not",
        "spherical",
        "wrong",
    ]
    count = 0
    for item in items:
        sentence = str(item.get("sentence", "")).lower().replace("\u2019", "'")
        if any(term in sentence for term in strong_terms):
            count += 1
    return count


def _decide_verdict(
    claim: str, evidence: Dict[str, List[dict]], sources: List[dict]
) -> str:
    if not sources:
        return "Insufficient Evidence"

    support = evidence.get("support", [])
    contradict = evidence.get("contradict", [])
    neutral = evidence.get("neutral", [])
    if not support and not contradict and not neutral:
        return "Insufficient Evidence"
    if not support and not contradict:
        return "Insufficient Evidence"

    support_strength = sum(float(item.get("score", 0)) for item in support)
    contradict_strength = sum(float(item.get("score", 0)) for item in contradict)

    if support and contradict:
        if _is_absolute_claim(claim):
            return "Mixed"
        strong_contradictions = _strong_contradiction_count(contradict)
        if strong_contradictions >= 2 and contradict_strength >= support_strength * 0.45:
            return "Contradicted"
        if support_strength >= contradict_strength * 2 and len(support) >= len(contradict) + 2:
            return "Supported"
        if contradict_strength >= support_strength * 2 and len(contradict) >= len(support) + 1:
            return "Contradicted"
        return "Mixed"

    if support:
        return "Supported"
    if contradict:
        return "Contradicted"
    return "Insufficient Evidence"


def check_claim(
    claim: str,
    model_bundle: Optional[Dict[str, object]] = None,
    generate_with_llm: bool = True,
) -> dict:
    """Run the full live-search fact-checking pipeline for one claim."""
    claim = clean_whitespace(claim)
    if len(claim) < 4:
        return _empty_result(claim, "Please enter a longer claim or question.")

    warnings: List[str] = []
    if is_sensitive_claim(claim):
        warnings.append("This is an automated evidence summary and not professional advice.")
    context_limited = is_context_limited_claim(claim)
    if context_limited:
        warnings.append(
            "This claim appears private, local, or highly context-dependent, so public web evidence may be insufficient."
        )

    search_results, search_error = search_web(claim)
    if search_error:
        warnings.append(search_error)

    sources = _build_sources(search_results)
    if not sources:
        message = (
            "Live web search did not return usable sources. Please check the "
            "connection or retry the claim."
        )
        return _empty_result(claim, message)

    page_results = []
    readable_pages = 0
    for result in search_results[:MAX_PAGES_TO_READ]:
        page = read_url(result.get("url", ""))
        page_results.append(page)
        if page.get("success"):
            readable_pages += 1

    if readable_pages == 0:
        warnings.append(
            "Page text could not be read from the top sources, so snippets were used."
        )

    evidence = extract_evidence(claim, search_results, page_results)
    verdict = _decide_verdict(claim, evidence, sources)
    confidence, confidence_text = calculate_confidence(sources, evidence)

    if context_limited:
        verdict = "Insufficient Evidence"
        confidence = min(confidence, 35)
        confidence_text = "Low"

    if verdict == "Insufficient Evidence":
        warnings.append(
            "The retrieved evidence is weak, missing, or too neutral for a confident verdict."
        )
    elif verdict == "Mixed":
        warnings.append("Sources or extracted evidence show disagreement.")

    try:
        if generate_with_llm:
            answer = generate_grounded_answer(
                claim,
                evidence,
                verdict,
                confidence,
                confidence_text,
                model_bundle=model_bundle,
                warnings=warnings,
            )
        else:
            answer = fallback_answer(
                claim, verdict, confidence, confidence_text, evidence, warnings
            )
    except Exception as exc:
        warnings.append(f"Local LLM generation failed, so a structured fallback was used: {exc}")
        answer = fallback_answer(
            claim, verdict, confidence, confidence_text, evidence, warnings
        )

    return {
        "claim": claim,
        "verdict": verdict,
        "answer": answer,
        "confidence": confidence,
        "confidence_label": confidence_text,
        "supporting_evidence": evidence.get("support", []),
        "contradicting_evidence": evidence.get("contradict", []),
        "neutral_evidence": evidence.get("neutral", []),
        "sources": sources,
        "warnings": warnings,
        "timestamp": current_timestamp(),
        "search_error": search_error,
    }
