# Fact-Checking Chatbot with Live Web Search and Evidence-Based Confidence Scoring

## 1. Title Page

**Project Title:** Fact-Checking Chatbot with Live Web Search and Evidence-Based Confidence Scoring

**Course:** Natural Language Processing

**Project Type:** End-to-end NLP application

**Main Technologies:** Python, Streamlit, Hugging Face Transformers, DuckDuckGo Search, Qwen/Qwen2.5-0.5B-Instruct

## 2. Abstract

The spread of online misinformation has created a need for tools that can help users inspect claims with evidence instead of relying only on memory or opinion. This project presents a web-based fact-checking chatbot that combines live web search, evidence extraction, transparent evidence classification, confidence scoring, and local language model generation. The system accepts a claim or question from the user, searches the live web through DuckDuckGo, retrieves source snippets and readable web page text, extracts relevant evidence sentences, classifies the evidence as supporting, contradicting, or neutral, and then uses a single local model, Qwen/Qwen2.5-0.5B-Instruct, to generate a concise answer. No paid API, API key, OpenAI model, Gemini model, Claude model, or hybrid model is used. The chatbot is designed as a university Natural Language Processing project and focuses on safe behavior: if evidence is weak, missing, or conflicting, the system says that evidence is insufficient instead of giving an unsupported answer. The final interface is built with Streamlit and presents a professional dark theme, final verdict, explanation, confidence score, evidence sections, source links, warnings, and search timestamp.

## 3. Introduction

Fact-checking is an important application of Natural Language Processing because people often encounter claims that are incomplete, exaggerated, false, or missing context. Search engines provide access to sources, but users still need to compare multiple pages, identify relevant statements, and understand whether sources agree or disagree. Large language models can summarize information, but when they answer from memory alone they may produce hallucinations or outdated statements. A practical fact-checking system should therefore combine retrieval with generation. Retrieval provides grounding, while generation helps explain the result in natural language.

This project implements that idea in a small but complete form. The chatbot does not simply ask a language model whether a claim is true. Instead, it performs live web search first. The retrieved evidence is shown to the user and also sent to the local LLM as context. The system is designed to be understandable for academic review: the evidence extraction and scoring logic are implemented with transparent rules, and the final result includes clickable sources. The project is also careful about limitations. For example, if live search fails or if the sources do not provide enough relevant evidence, the verdict becomes "Insufficient Evidence."

## 4. Problem Statement

Many fact-checking tools depend on external APIs, large commercial models, or hidden ranking systems. These approaches can be difficult to reproduce in a university environment. They may also require paid credentials or internet services that are not available to every student. Another problem is that generative models can answer confidently even when they do not have reliable evidence. This creates a risk of hallucination, especially for recent events, health claims, scientific claims, and claims involving private or local information.

The problem addressed by this project is how to build a complete, reproducible, no-API-key fact-checking chatbot that uses live web evidence and one local LLM while still remaining safe when evidence is weak. The system must be usable in a browser, understandable to a reviewer, and ready for university submission.

## 5. Objectives

The first objective is to build a working web application where a user can enter a claim and receive a fact-checking result. The second objective is to ground answers in live web evidence rather than model memory. The third objective is to use only one local Hugging Face LLM, Qwen/Qwen2.5-0.5B-Instruct, for final answer generation. The fourth objective is to provide a confidence score based on evidence strength, number of sources, source diversity, agreement level, and keyword overlap. The fifth objective is to create documentation, evaluation data, a report, and code structure suitable for academic submission.

## 6. Literature and Background

Fact-checking systems commonly use information retrieval, natural language inference, claim verification, and evidence ranking. In classical information retrieval, a query is matched against documents, and the most relevant documents are returned. In evidence-based NLP, a system must not only find documents but also locate the specific text that supports or contradicts a claim. Research datasets for fact verification, such as FEVER-style tasks, often separate the task into document retrieval, sentence selection, and claim classification.

Recent language models can produce fluent explanations, but they are not always reliable as standalone fact sources. Retrieval-augmented generation is a common design pattern where external documents are retrieved first and then provided to a model as context. This reduces hallucination because the model is asked to generate from supplied evidence. In this project, the same principle is applied with live web search and a small local instruction model. The system keeps the classification and confidence scoring transparent so the final answer can be inspected.

## 7. Proposed System

The proposed system is a Streamlit application called "Fact-Checking Chatbot." It has a modern dark user interface with a claim input box, example claim buttons, and result cards. When a claim is submitted, the backend searches DuckDuckGo without requiring an API key. It retrieves a limited number of results to control speed and avoid unnecessary network requests. For the top sources, the system tries to fetch page text. It uses trafilatura to extract readable article text and BeautifulSoup as a fallback.

After retrieval, the system extracts candidate evidence sentences from both snippets and page text. It ranks sentences using keyword overlap with the claim. It then classifies each sentence with rule-based lexical logic. Sentences containing contradiction cues such as "false," "myth," "not," "no evidence," or "debunked" may be classified as contradicting. Sentences containing support cues such as "according to," "shows," "study," "reported," or "official" may be classified as supporting. Sentences that are related but uncertain are classified as neutral.

The system then decides a preliminary verdict: Supported, Contradicted, Mixed, or Insufficient Evidence. It calculates a confidence score from the amount and agreement of evidence. Finally, the evidence and preliminary result are passed to the local Qwen model with a strict prompt that instructs the model to answer only from the provided evidence.

## 8. System Architecture

The architecture has five main layers. The first layer is the frontend, implemented in `app.py` using Streamlit. It collects user input and displays the final output. The second layer is search and retrieval, implemented in `search_engine.py` and `web_reader.py`. The third layer is evidence processing, implemented in `evidence_extractor.py`. The fourth layer is decision and scoring, implemented in `fact_checker.py` and `scoring.py`. The fifth layer is generation, implemented in `llm_utils.py`.

The main orchestration function is `check_claim(claim: str) -> dict`. This function returns a structured dictionary containing the original claim, verdict, answer, confidence, supporting evidence, contradicting evidence, neutral evidence, source links, warnings, and timestamp. This structure allows both the Streamlit app and the evaluation script to use the same backend.

## 9. Methodology

The method begins with input validation. Very short or empty inputs are rejected with a clean message. The claim is cleaned by normalizing whitespace. The search module then queries DuckDuckGo and returns a list of dictionaries containing title, URL, and snippet. URLs are deduplicated, and invalid results are removed.

The web reader attempts to retrieve readable text from the top search results. It uses a timeout so the app does not hang on slow websites. It skips binary files and unsupported content types. If a page cannot be read, the system still uses the search snippet. This is important because many websites block scraping, load content dynamically, or require JavaScript. The system should not crash because one page fails.

Evidence extraction is performed by splitting text into sentences and ranking them by keyword overlap. This is a simple method, but it is transparent and suitable for a university project. Each evidence sentence includes a score, title, and URL. The final evidence lists are separated into supporting, contradicting, and neutral groups.

## 10. LLM Selection and Local Deployment

The project uses Qwen/Qwen2.5-0.5B-Instruct as the only LLM. This model is small enough to run locally on many machines, especially compared with larger instruction models. It is loaded using Hugging Face Transformers with `AutoTokenizer` and `AutoModelForCausalLM`. CUDA is used automatically if available, otherwise CPU is used. The tokenizer pad token is set to the end-of-sequence token if no pad token exists.

The local model is used only after web evidence has been retrieved and organized. It is not used as a standalone fact database. The prompt includes the claim, grouped evidence, source titles and URLs, preliminary verdict, confidence score, and warnings. The system message tells the model to answer only using the provided web evidence and to say that evidence is insufficient when evidence is weak. In Streamlit, the model is cached with `st.cache_resource` so it does not reload after every question.

## 11. Web Search and Evidence Retrieval

The search module uses DuckDuckGo search without an API key. It first tries the package interface from `duckduckgo-search`, with a fallback import for newer package naming. If package search fails, the system attempts a simple HTML fallback. This makes the project more robust because package interfaces can change over time.

For each result, the title, URL, and snippet are stored. The web reader fetches selected pages using a browser-like user agent. It extracts readable text with trafilatura when possible because trafilatura is designed for web article extraction. If that fails, BeautifulSoup extracts paragraph text. The text is cleaned and truncated to the configured maximum number of characters to keep the application fast.

## 12. Evidence Classification

Evidence classification uses a transparent rule-based method. The claim and candidate sentence are tokenized into keywords. The overlap between claim keywords and sentence keywords gives a relevance score. If the score is too low, the sentence is treated as neutral or ignored. If the sentence contains contradiction terms, the system may classify it as contradicting. If it contains support terms, it may classify it as supporting. Negation is also considered, because a sentence such as "the Earth is not flat" contradicts the claim "The Earth is flat."

This classification method is not as powerful as a trained natural language inference model. However, the project requirement states that only one LLM should be used and no hybrid model should be added. Therefore, rule-based classification is a suitable choice. It keeps the system simple, reproducible, and explainable.

## 13. Confidence Scoring

The confidence score is calculated in `scoring.py`. It starts from a base score and adds points for the number of sources, number of relevant evidence sentences, source diversity, agreement consistency, and keyword overlap. It subtracts points when supporting and contradicting evidence both exist or when relevant evidence is very weak. The final score is clamped between 0 and 100. Scores from 0 to 39 are labeled Low, 40 to 69 Medium, and 70 to 100 High.

The confidence score is not a mathematical proof of truth. It is an evidence-strength signal. A high score means that the retrieved evidence is relatively strong and consistent. A low score means that the system found little evidence, weak evidence, or disagreement.

## 14. User Interface

The user interface is built with Streamlit and custom CSS. It uses a dark modern theme with cards, status pills, example claim buttons, a clear input area, and organized output sections. The result includes a verdict card, confidence score card, final answer card, supporting evidence card, contradicting evidence card, neutral evidence card, sources card, warnings card, and search timestamp. Source links are clickable so users can inspect the original web pages.

The interface also includes "About this Project" and "How It Works" sections. These explain that the system uses live web search, evidence extraction, evidence classification, local LLM explanation, and confidence scoring. The UI avoids raw JSON and shows clean messages when errors occur.

## 15. Evaluation Methodology

The evaluation file contains at least 20 claims. The claims are divided into generally true, generally false, mixed or partially true, and insufficient evidence categories. Each row contains a claim, expected verdict, and category. The evaluation script runs the same `check_claim` pipeline used by the app. It saves detailed results to `results/evaluation_results.csv` and summary metrics to `results/evaluation_summary.md`.

The measured metrics are total claims tested, verdict accuracy compared with expected verdict, average confidence, number of successful searches, and number of insufficient evidence predictions. The system does not fake evaluation results. Since search is live, results can change depending on time, region, network behavior, and search engine availability.

## 16. Results and Findings

The final results should be generated by running `python -m src.evaluation`. The expected behavior is that common scientific and health claims with strong public evidence should return useful sources and evidence. Claims such as "The Earth is flat" should usually be contradicted by reliable sources. Claims such as "Exercise can improve mental health" should usually be supported. Mixed claims, such as "Electric cars produce zero emissions," may produce both supporting and contradicting evidence because electric vehicles have no tailpipe emissions but still have manufacturing and electricity-related emissions. Private or highly local claims should usually produce insufficient evidence.

The most important finding is that live evidence improves safety. Instead of producing an answer from model memory alone, the system shows the sources and evidence used. Another finding is that small local models can be useful for explanation when retrieval and scoring are handled separately. However, the quality of the final answer depends heavily on the quality of retrieved evidence.

## 17. Limitations

This project has several limitations. First, live search can fail because of network problems, search engine rate limits, or package changes. Second, web pages may block automated requests or use dynamic content that is not visible to `requests`. Third, rule-based evidence classification can miss complex meaning, sarcasm, numerical comparisons, or claims requiring deep context. Fourth, Qwen/Qwen2.5-0.5B-Instruct is a small model, so it may produce less polished explanations than larger models. Fifth, a confidence score based on retrieved evidence is not the same as objective truth.

The system is also not a replacement for professional medical, legal, or financial advice. For sensitive claims, it adds a warning that the output is an automated evidence summary and not professional advice.

## 18. Conclusion

This project successfully designs and implements an end-to-end NLP fact-checking chatbot using live web search, evidence extraction, rule-based evidence classification, confidence scoring, and one local LLM. The use of Qwen/Qwen2.5-0.5B-Instruct satisfies the requirement for a local Hugging Face model without paid APIs or API keys. The system is grounded in web evidence and includes safety behavior for weak or conflicting evidence. The Streamlit frontend makes the tool accessible in a browser and suitable for a university demo.

The project demonstrates how information retrieval and language generation can work together. Search provides current evidence, rule-based methods organize and score that evidence, and the local LLM explains the result in readable language. Although the system has limitations, it provides a complete and reproducible foundation for evidence-based fact-checking.

## 19. References

- Hugging Face Transformers documentation: https://huggingface.co/docs/transformers
- Qwen/Qwen2.5-0.5B-Instruct model card: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct
- Streamlit documentation: https://docs.streamlit.io/
- DuckDuckGo Search package documentation: https://pypi.org/project/duckduckgo-search/
- Thorne, J., Vlachos, A., Christodoulopoulos, C., and Mittal, A. FEVER: a large-scale dataset for fact extraction and verification.
- Manning, C. D., Raghavan, P., and Schutze, H. Introduction to Information Retrieval.
- Lewis, P. et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.

