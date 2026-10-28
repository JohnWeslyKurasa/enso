# AI Usage Report: Thelawala Search

This document outlines how AI tools and agentic coding workflows were utilized in the development of the Thelawala search engine, the instructions provided, where AI assistance required course-correction, and how issues were verified.

---

## 1. How AI Tools Were Used

AI was used as an active pair-programming partner across the software engineering lifecycle:

1. **Exploratory Data Analysis (EDA):**
   - Writing automated inspection scripts to analyze distributions, missing values, and anomalies across `catalog.csv`, `inventory.csv`, and `search_log.jsonl`.
   - Identifying the root causes behind the 42.3% zero-result search rate in historical customer logs.

2. **System Architecture & Rule Formulation:**
   - Translating conflicting team requirements from `emails.md` into concrete, mathematically bounded ranking signals (balancing Kavya's brand priority, Sandeep's stock caution, Farah's margin and click data, and Arjun's strict runtime constraints).

3. **Core Search Engine Implementation:**
   - Drafting the BM25 inverted index, Levenshtein typo-tolerance algorithms, natural language price parser, and multi-signal ranker in pure Python (avoiding external runtime network dependencies).

4. **Interface & Test Suite Creation:**
   - Implementing both the automated batch runner (`batch_search.py`), an interactive CLI tool (`cli.py`), a modern glassmorphic Web UI (`web_app.py`), and regression tests.

---

## 2. Main Prompts and Instructions

### Prompt 1: Initial Discovery & Objective Breakdown
> *"I have got an assignment from a company, can you tell me what I have to do exactly?"*
>
> **Intent:** Deconstruct the email thread and assignment guidelines to define core deliverables, technical constraints, and evaluation rubrics before writing code.

### Prompt 2: Data Exploration & Anomaly Detection
> *"Inspect catalog.csv, inventory.csv, and search_log.jsonl. Why did 42.3% of searches return 0 results, why did Sandeep say prices looked wrong, and why did 'milk' fail?"*
>
> **Outcome:** Revealed that `metro_feed` was priced in paise (₹167 dal was entered as `16700`), customer queries in Hyderabad frequently used Telugu terms (`paalu`, `venna`, `biyyam pindi`) or price constraints (`oil under 200`), and naive search matched milk chocolate before fresh dairy milk.

### Prompt 3: Building the Search Engine & Batch Runner
> *"Build the complete, modular search engine in pure Python. Ensure zero external API calls at query time, sub-5ms latency, support for batch evaluation outputting results.jsonl, a CLI, and a Web UI."*
>
> **Outcome:** Structured the system into `thelawala_search/` package, created `batch_search.py`, `cli.py`, and `web_app.py`.

---

## 3. Where AI Got Things Wrong & How It Was Caught

### Mistake 1: Windows Terminal Character Encoding (`charmap` / `cp1252`)
- **What happened:** In initial test scripts and print routines, the AI inserted the Indian Rupee symbol (`₹`) and Telugu Unicode characters directly into standard `print()` statements. On the Windows host system running Python 3.13, this crashed the test runner with:
  ```
  UnicodeEncodeError: 'charmap' codec can't encode character '\u20b9' in position 83: character maps to <undefined>
  ```
- **How it was caught:** Immediate execution of `python test_search_engine.py` caught the runtime crash.
- **The fix:** Configured `sys.stdout.reconfigure(encoding='utf-8')` across all entrypoints and used resilient fallbacks for Windows console compatibility.

### Mistake 2: Over-Boosting Store Brand (Violating Founder's Principle)
- **What happened:** In the first draft of the scoring function, the AI applied a flat $+3.0$ boost to all `"Thela Select"` private label items to satisfy Farah's margin request. However, when testing the query `"godavari milk"`, the private label `"Thela Select Full Cream Milk"` ranked above `"Godavari Dairy Toned Milk"`.
- **How it was caught:** We reviewed Kavya's email explicitly stating: *"If someone searches for a brand, show them that brand. Customer first, margin second."*
- **The fix:** Updated `ranker.py` with brand intent detection. If a user explicitly specifies a brand (e.g. `Godavari`, `Ammas Kitchen`), that brand receives a $+10.0$ priority boost and competing brands are de-ranked; private label boost is enabled *only* on generic or category-level searches (e.g., *"bread"*, *"curd"*, *"ghee"*).

### Mistake 3: Python Module Import Resolution in Standalone Tests
- **What happened:** The AI placed unit tests in `tests/test_api_and_engine.py` and attempted to import `from thelawala_search.engine import ThelawalaSearchEngine`. When invoked directly with `python tests/test_api_and_engine.py`, Python raised:
  ```
  ModuleNotFoundError: No module named 'thelawala_search'
  ```
- **How it was caught:** Running the test suite from the terminal immediately highlighted the missing parent path.
- **The fix:** Added `sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))` to ensure tests execute cleanly whether run via standard python or test runners.

### Mistake 4: Dependency Assumptions (`pytest`)
- **What happened:** The initial test script imported `pytest`. However, `pytest` was not installed in the user's local Python environment.
- **How it was caught:** Running the script raised `ModuleNotFoundError: No module named 'pytest'`.
- **The fix:** Rewrote the test assertions using Python's standard library and assertions, ensuring zero installation friction for the evaluator.

---

## 4. Evaluation & Verification Methodology

Every component was tested against real queries from `search_log.jsonl`:
1. **Regression Assertions:** Verified `"milk"` returns 100% dairy milk packets (zero chocolates, zero biscuits).
2. **Price Filter Bounds:** Verified all items returned for `"oil under 200"` have `price <= 200.0`.
3. **Throughput:** Verified `batch_search.py` processes queries at > 750 queries/second.
4. **Stock Ordering:** Verified in-stock items strictly precede out-of-stock items.
