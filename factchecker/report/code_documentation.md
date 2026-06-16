# Code Documentation

## app.py

`app.py` contains the Streamlit frontend. It defines the page configuration, custom CSS, hero section, claim input, example claim buttons, result display cards, evidence sections, warnings, sources, and project information sections. It also caches the local Qwen model with `st.cache_resource` so the model is not reloaded for every user query.

## config.py

`config.py` centralizes project constants such as the model name, search limits, page text limits, generation settings, request timeout, app title, data directory, and results directory. Keeping these values in one place makes the system easier to tune for demos or slower machines.

## src/search_engine.py

`search_engine.py` performs DuckDuckGo web search without an API key. It first tries the current `duckduckgo-search` package interface and includes a fallback for the newer `ddgs` import style. If package-based search fails, it attempts a simple DuckDuckGo HTML search fallback. The module normalizes titles, URLs, and snippets, removes duplicate URLs, and returns errors without crashing the app.

## src/web_reader.py

`web_reader.py` fetches source pages with `requests` using a browser-like user agent and a timeout. It skips binary files and unsupported content types. For readable HTML pages, it tries `trafilatura` first and falls back to BeautifulSoup paragraph extraction. The extracted text is cleaned and limited to the configured maximum length.

## src/evidence_extractor.py

`evidence_extractor.py` splits snippets and page text into candidate sentences. It ranks sentences by keyword overlap with the claim and removes duplicates. Each evidence sentence keeps its source title and URL. The module classifies evidence as support, contradict, or neutral using transparent lexical rules such as support terms, contradiction terms, negation, and keyword overlap.

## src/fact_checker.py

`fact_checker.py` orchestrates the full pipeline. The public function `check_claim(claim: str) -> dict` validates the claim, runs search, reads pages, extracts evidence, decides the preliminary verdict, calculates confidence, calls the local Qwen model for a grounded answer, and returns a structured result dictionary for the UI or evaluation script.

## src/llm_utils.py

`llm_utils.py` loads `Qwen/Qwen2.5-0.5B-Instruct` with Hugging Face Transformers. It selects CUDA automatically when available and CPU otherwise. It sets the tokenizer pad token when needed, formats a strict grounded prompt, uses `apply_chat_template` when supported, and generates a concise evidence-based explanation. If generation fails, a deterministic fallback answer is available.

## src/scoring.py

`scoring.py` calculates the confidence score. The score considers source count, source diversity, relevant evidence count, agreement between supporting and contradicting evidence, keyword overlap, and penalties for weak or conflicting evidence. It clamps the final score between 0 and 100 and maps it to Low, Medium, or High.

## src/evaluation.py

`evaluation.py` loads test claims from `data/evaluation_claims.jsonl`, runs the fact-checking pipeline, saves detailed rows to `results/evaluation_results.csv`, and writes a Markdown summary to `results/evaluation_summary.md`. It reports total claims tested, verdict accuracy, average confidence, successful searches, and insufficient evidence cases. It does not fake results.

## src/utils.py

`utils.py` provides shared helper functions for whitespace cleaning, keyword tokenization, keyword overlap scoring, URL validation, source deduplication, domain extraction, timestamp generation, sensitive-claim detection, and numeric clamping.
It also detects highly private or context-limited claims so the fact checker can safely return insufficient evidence when public web results are likely generic.

## Data Files

`data/sample_claims.jsonl` contains sample claims used by the app and README. `data/evaluation_claims.jsonl` contains at least 20 labeled claims across supported, contradicted, mixed, and insufficient evidence categories. Each row includes a claim, expected verdict, and category.

## Results Folder

The `results` folder stores outputs from evaluation. `evaluation_results.csv` is generated during evaluation and ignored by Git. `evaluation_summary.md` is kept as a readable summary for university submission and is updated whenever evaluation is run.

## Report Folder

The `report` folder contains the academic term paper and this code documentation file. These files explain the design, methodology, implementation, limitations, and project structure.
