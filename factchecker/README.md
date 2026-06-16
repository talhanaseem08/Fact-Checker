# Fact-Checking Chatbot with Live Web Search and Evidence-Based Confidence Scoring

## Project Overview

This is a complete Natural Language Processing university project that builds a web-based fact-checking chatbot. A user enters a claim or question, the system searches the live web, retrieves source snippets and readable page text, extracts relevant evidence sentences, classifies evidence as supporting, contradicting, or neutral, and then generates a grounded final explanation with one local Hugging Face model: `Qwen/Qwen2.5-0.5B-Instruct`.

The project does not use OpenAI, Gemini, Claude, paid APIs, or API keys. Web search is used for grounding so the model is not treated as the only source of truth.

## Features

- Streamlit browser frontend with a polished dark interface
- Live DuckDuckGo web search without an API key
- Web page reading with `requests`, `trafilatura`, and BeautifulSoup fallback
- Evidence sentence extraction using keyword overlap
- Transparent rule-based evidence classification
- Single local Qwen LLM for final answer generation
- Evidence-based confidence score and label
- Clear insufficient evidence behavior
- Clickable source links
- Evaluation script with CSV and Markdown outputs
- Ready-to-submit README, report, code documentation, data files, and screenshot instructions

## Tech Stack

- Python
- Streamlit
- Hugging Face Transformers
- Qwen/Qwen2.5-0.5B-Instruct
- DuckDuckGo search without API key
- requests
- BeautifulSoup4
- trafilatura
- pandas
- numpy
- scikit-learn
- torch

## Folder Structure

```text
fact-checking-chatbot/
|-- README.md
|-- requirements.txt
|-- .gitignore
|-- config.py
|-- app.py
|-- src/
|   |-- __init__.py
|   |-- search_engine.py
|   |-- web_reader.py
|   |-- evidence_extractor.py
|   |-- fact_checker.py
|   |-- llm_utils.py
|   |-- scoring.py
|   |-- evaluation.py
|   `-- utils.py
|-- data/
|   |-- sample_claims.jsonl
|   `-- evaluation_claims.jsonl
|-- results/
|   |-- README.md
|   `-- evaluation_summary.md
|-- report/
|   |-- term_paper.md
|   `-- code_documentation.md
`-- screenshots/
    `-- README.md
```

## How the System Works

1. The user enters a claim or question in Streamlit.
2. The input is cleaned and validated.
3. DuckDuckGo search retrieves live web results.
4. The top pages are fetched and converted into readable text where possible.
5. The system extracts evidence sentences from snippets and page text.
6. Evidence is ranked by keyword overlap with the claim.
7. Evidence is classified as supporting, contradicting, or neutral with transparent lexical rules.
8. A preliminary verdict is calculated from evidence balance.
9. A confidence score is calculated from source count, source diversity, evidence count, agreement, and keyword overlap.
10. Qwen/Qwen2.5-0.5B-Instruct generates a concise final explanation grounded in the retrieved evidence.
11. The UI displays the verdict, confidence score, final answer, evidence groups, warnings, source links, and timestamp.

## Installation

Create a virtual environment.

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Mac/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The first run may download the local Qwen model from Hugging Face. This can take time depending on the internet connection.

## Running the App

```bash
streamlit run app.py
```

If Streamlit is not recognized:

```bash
python -m streamlit run app.py
```

Open in browser:

```text
http://localhost:8501
```

## Running Evaluation

```bash
python -m src.evaluation
```

The evaluation reads `data/evaluation_claims.jsonl`, runs the live fact-checking pipeline, and writes:

- `results/evaluation_results.csv`
- `results/evaluation_summary.md`

Evaluation results are not hard-coded because web search results can change.

## No API Key Requirement

This project does not require an API key. It uses DuckDuckGo search without an API key and a local Hugging Face model for answer generation.

## Local LLM Explanation

The only LLM used is `Qwen/Qwen2.5-0.5B-Instruct`. It is loaded with Hugging Face Transformers in `src/llm_utils.py`. The model is cached by Streamlit so it does not reload on every claim. CUDA is used automatically if available; otherwise, CPU is used.

The model receives a strict grounded prompt containing the claim, grouped evidence, source titles, source URLs, preliminary verdict, confidence score, and warnings. It is instructed to answer only from the provided evidence.

## Limitations

- Live web search may fail because of network issues, temporary search limits, or blocked pages.
- Some pages cannot be read because they are PDFs, scripts, paywalled pages, or protected by bot checks.
- Rule-based evidence classification is transparent but not perfect.
- Qwen/Qwen2.5-0.5B-Instruct is a small local model, so explanations may be less fluent than larger paid models.
- The system is not a replacement for professional medical, legal, or financial advice.
- Claims about private, local, or very recent events may produce insufficient evidence.
- Private or highly context-dependent claims are intentionally treated cautiously because public web results may be generic or unrelated.

## Troubleshooting

If Streamlit is not recognized:

```bash
python -m streamlit run app.py
```

If model download is slow, wait for Hugging Face download to finish or run again after the connection improves.

If search returns no results, retry the claim, check the internet connection, or try a more specific claim.

If page reading fails, the system still uses search snippets when available.

If `duckduckgo-search` changes its import style, `src/search_engine.py` already includes fallback handling.

## Example Claims

- The Earth is flat.
- Exercise can improve mental health.
- AI will completely replace all programmers.
- Drinking 8 glasses of water daily is necessary for everyone.
- Electric cars produce zero emissions.
- Coffee is always bad for health.
