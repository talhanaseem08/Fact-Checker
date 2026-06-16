from typing import Dict, List, Optional

from config import BASE_MODEL_NAME, MAX_NEW_TOKENS, TEMPERATURE, TOP_P


SYSTEM_MESSAGE = (
    "You are a careful fact-checking assistant. You must answer only using the "
    "provided web evidence. Do not use unsupported claims. If evidence is weak, "
    "say that evidence is insufficient. Give a clear verdict and short explanation."
)


def load_local_llm(model_name: str = BASE_MODEL_NAME) -> Dict[str, object]:
    """Load the single local Hugging Face model used by the project."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    try:
        model = AutoModelForCausalLM.from_pretrained(model_name, dtype=dtype)
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=dtype)
    model.to(device)
    model.eval()

    return {"tokenizer": tokenizer, "model": model, "device": device, "model_name": model_name}


def _format_evidence(items: List[dict], label: str) -> str:
    if not items:
        return f"{label}: None found."
    lines = [f"{label}:"]
    for index, item in enumerate(items[:8], start=1):
        lines.append(
            f"{index}. {item.get('sentence', '')} "
            f"(Source: {item.get('title', 'Untitled')} - {item.get('url', '')})"
        )
    return "\n".join(lines)


def build_prompt(
    claim: str,
    evidence: Dict[str, List[dict]],
    preliminary_verdict: str,
    confidence: int,
    confidence_text: str,
    warnings: Optional[List[str]] = None,
) -> List[dict]:
    warning_text = "\n".join(f"- {warning}" for warning in warnings or []) or "None"
    user_message = f"""
Claim:
{claim}

Preliminary verdict:
{preliminary_verdict}

Calculated confidence:
{confidence}/100 ({confidence_text})

Evidence:
{_format_evidence(evidence.get("support", []), "Supporting evidence")}

{_format_evidence(evidence.get("contradict", []), "Contradicting evidence")}

{_format_evidence(evidence.get("neutral", []), "Neutral or related evidence")}

Warnings:
{warning_text}

Write the final answer with these headings:
Verdict:
Explanation:
What the evidence says:
Confidence:
Limitations:
""".strip()
    return [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": user_message},
    ]


def generate_grounded_answer(
    claim: str,
    evidence: Dict[str, List[dict]],
    preliminary_verdict: str,
    confidence: int,
    confidence_text: str,
    model_bundle: Optional[Dict[str, object]] = None,
    warnings: Optional[List[str]] = None,
) -> str:
    """Generate a concise final answer with the single local Qwen model."""
    if model_bundle is None:
        model_bundle = load_local_llm()

    tokenizer = model_bundle["tokenizer"]
    model = model_bundle["model"]
    device = model_bundle["device"]
    messages = build_prompt(
        claim,
        evidence,
        preliminary_verdict,
        confidence,
        confidence_text,
        warnings=warnings,
    )

    try:
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    except Exception:
        text = (
            f"System: {messages[0]['content']}\n"
            f"User: {messages[1]['content']}\n"
            "Assistant:"
        )

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=4096,
    )
    inputs = {key: value.to(device) for key, value in inputs.items()}

    import torch

    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            pad_token_id=tokenizer.eos_token_id,
        )

    prompt_length = inputs["input_ids"].shape[-1]
    new_tokens = generated[0][prompt_length:]
    answer = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    return answer or fallback_answer(claim, preliminary_verdict, confidence, confidence_text, evidence, warnings)


def fallback_answer(
    claim: str,
    verdict: str,
    confidence: int,
    confidence_text: str,
    evidence: Dict[str, List[dict]],
    warnings: Optional[List[str]] = None,
) -> str:
    support_count = len(evidence.get("support", []))
    contradict_count = len(evidence.get("contradict", []))
    neutral_count = len(evidence.get("neutral", []))
    warning_sentence = ""
    if warnings:
        warning_sentence = " Limitations: " + " ".join(warnings[:2])
    return (
        f"Verdict: {verdict}\n\n"
        f"Explanation: The system reviewed live web search results for the claim: "
        f"'{claim}'. It found {support_count} supporting, {contradict_count} "
        f"contradicting, and {neutral_count} neutral evidence sentences.\n\n"
        f"What the evidence says: The verdict is based on the balance of retrieved "
        f"evidence, source diversity, and keyword overlap with the claim.\n\n"
        f"Confidence: {confidence}/100 ({confidence_text}).{warning_sentence}"
    )
