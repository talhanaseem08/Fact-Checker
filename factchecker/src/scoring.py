from typing import Dict, List

from .utils import clamp, safe_domain


def confidence_label(score: int) -> str:
    if score < 40:
        return "Low"
    if score < 70:
        return "Medium"
    return "High"


def calculate_confidence(
    sources: List[dict], evidence: Dict[str, List[dict]]
) -> tuple[int, str]:
    support = evidence.get("support", [])
    contradict = evidence.get("contradict", [])
    neutral = evidence.get("neutral", [])
    relevant = support + contradict

    if not sources:
        return 5, "Low"

    score = 20.0

    source_count = len(sources)
    score += min(source_count, 5) * 5

    relevant_count = len(relevant)
    score += min(relevant_count, 5) * 5

    domains = {safe_domain(source.get("url", "")) for source in sources}
    domains.discard("")
    score += min(len(domains), 5) * 3

    if relevant:
        support_strength = sum(float(item.get("score", 0)) for item in support)
        contradict_strength = sum(float(item.get("score", 0)) for item in contradict)
        total_strength = support_strength + contradict_strength
        agreement = max(support_strength, contradict_strength) / total_strength if total_strength else 0
        score += agreement * 20
        avg_overlap = sum(float(item.get("overlap", 0)) for item in relevant) / len(relevant)
        score += min(avg_overlap, 1.0) * 10
    elif neutral:
        score += min(len(neutral), 4) * 2
        score -= 20
    else:
        score -= 25

    if support and contradict:
        score -= 15

    if relevant_count < 2:
        score -= 15

    final_score = clamp(score)
    return final_score, confidence_label(final_score)

