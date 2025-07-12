Below is a comprehensive, end-to-end deep dive on building an Origami-style AI agent website for scraping arbitrary real-estate sites—powered by the Q2\_K–quantized LLaMA-2 7B model. We’ll cover **only** the scraping engine itself and its integration with the quantized LLM, from planning through extraction, error-handling, scaling, and web-app orchestration.

---

## 1. High-Level Architecture

```
┌──────────────┐     HTTP/API    ┌──────────────┐
│   Frontend   │◀──────────────▶│   Backend    │
│ (Next.js/    │                │ (FastAPI/    │
│  React)      │                │  Flask, etc.)│
└──────┬───────┘                └──────┬───────┘
       │                                │
       │   enqueue “scrape job”         │
       ▼                                │
┌──────────────┐      work queue      ┌─▼────────────┐
│  Task Queue  │◀────────────────────▶│  Worker(s)   │
│ (Redis/Rabbit)│                     │  (Python)    │
└──────┬───────┘                       └─┬────────────┘
       │                                  │
       │                                  │
       │    results & logs                │
       ▼                                  ▼
┌──────────────┐                     ┌──────────────┐
│  Data Store  │                     │  Vector DB   │
│ (Postgres /  │                     │ (Chroma/     │
│  S3 / Files) │                     │  FAISS)      │
└──────────────┘                     └──────────────┘
```

**Key components**:

1. **Frontend** – Job creation UI, status dashboard, result viewer.
2. **Backend API** – Auth, enqueueing, status endpoints.
3. **Task Queue** – Distributes scrape jobs to workers.
4. **Worker** – Runs the agent loop:

   * **Planning** via Q2\_K LLM
   * **Execution** via Playwright
   * **Extraction** via LLM + heuristics
   * **Persistence** of results & memory
5. **Vector DB** – Stores per-domain “flows” for RAG-style recovery.

---

## 2. Agent Loop & Scraping Pipeline

### 2.1. Job Definition

A “job” encapsulates:

* **Target URL**
* **Domain identifier** (e.g. `zillow.com`)
* **Optional credentials** (for login flows)
* **Extraction schema placeholder** (ignored here)

### 2.2. Loop Steps

```text
for each job:
  1. Initialize headless browser context
  2. Load page URL (wait for networkidle)
  3. Capture HTML snapshot
  4. Plan actions via Q2_K (scroll, click, login, paginate…)
  5. Execute each action (with stealth + humanization)
     └─ after each action: wait, capture any new HTML
  6. Once settled: extract data fields
     └─ via LLM or CSS/XPath heuristics
  7. If extraction incomplete:
     └─ retrieve past “flow” from Vector DB (RAG)
     └─ retry with updated plan or fallback rules
  8. Persist JSON results + logs + raw HTML
  9. Close browser, mark job done/failed
```

---

## 3. Planning with Q2\_K

### 3.1. Why Q2\_K?

* **\~2.8 GB** on-disk, leaves \~5 GB RAM free.
* Fast inference (\~50 ms/token) on M2 CPU.
* Sufficient for short–prompt reasoning (3–5 actions).

### 3.2. Prompt Design

```python
from llama_cpp import Llama

llm = Llama(model_path="Llama-2-7B.Q2_K.gguf", n_threads=4)

def plan_actions(html_snippet: str, goal: str="extract listings"):
    prompt = f"""
You are an autonomous browser agent planning a sequence of user-like actions
(click, scroll, input) to achieve the goal: {goal}.
Here is an HTML snapshot of the page:
```

{html\_snippet}

```
List numbered steps in JSON: [
  {{ "action": "scroll", "params": {{ "by": "page_bottom" }} }},
  {{ "action": "click",  "params": {{ "selector": "CSS or XPath" }} }}
].
"""
    resp = llm(prompt, max_tokens=256, temperature=0.0)
    return resp["choices"][0]["text"]
```

**Best practices**:

* **HTML snippet length**: truncate to \~2 K characters around `<body>…</body>` or around known content regions.
* **Temperature=0**: deterministic plans.
* **JSON output**: easy to parse and validate.

---

## 4. Browser Automation & Execution

### 4.1. Playwright + Stealth

```bash
pip install playwright playwright-stealth
playwright install chromium
```

```python
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

def run_actions(actions, url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context()
        page    = ctx.new_page()
        stealth_sync(page)
        page.goto(url, wait_until="networkidle")

        for step in actions:
            act, params = step["action"], step["params"]
            if act == "scroll":
                page.evaluate("() => window.scrollBy(0, document.body.scrollHeight)")
            elif act == "click":
                page.click(params["selector"], timeout=5000)
            elif act == "input":
                page.fill(params["selector"], params["text"])
            page.wait_for_timeout(params.get("delay", 500))

        html = page.content()
        browser.close()
        return html
```

### 4.2. Human-Like Interaction

```python
import random, time

def human_click(page, selector):
    box = page.query_selector(selector).bounding_box()
    x = box["x"] + random.uniform(5, box["width"]-5)
    y = box["y"] + random.uniform(5, box["height"]-5)
    page.mouse.move(x, y, steps=5)
    page.mouse.click(x, y)
    time.sleep(random.uniform(0.3, 1.0))
```

---

## 5. Selector Generation & Data Extraction

### 5.1. LLM-Guided Extraction

Use Q2\_K to map “where is the price?” to a CSS/XPath selector:

```python
def extract_with_llm(html_snippet, field_name="price"):
    prompt = f"""
You are extracting the field "{field_name}" from this HTML:
```

{html\_snippet}

```
Return a CSS selector that matches the price element.
"""
    out = llm(prompt, max_tokens=128, temperature=0.0)
    selector = out["choices"][0]["text"].strip()
    return selector
```

### 5.2. Heuristic Fallbacks

* **Regex** on text nodes (e.g., `\$\d{2,4}` for prices).
* **Attribute search**: look for `aria-label`, `data-*`, common class substrings (`.price`, `.addr`).
* **Document.querySelectorAll** + filter by text pattern.

---

## 6. Resilience & Error Handling

### 6.1. RAG-Style Recovery

* **Embed** failed HTML+selectors into Vector DB.
* **At retry**, retrieve nearest past “flow” for this domain and adapt.

### 6.2. Selector Versioning

* Store each successful selector with timestamp.
* On failure, try last N versions in descending recency.

### 6.3. Visual Diffing

* **Screenshot** key regions (list container) and compare histograms or structural fingerprints to detect UI shifts.

### 6.4. Automated Retries

* On network errors or missing selectors, back off (`exp-backoff`) and reattempt up to 3×.

---

## 7. Anti-Bot Evasion

1. **playwright-stealth** to mask headless flags.
2. **Rotate User-Agent** per context:

   ```python
   ctx = browser.new_context(user_agent=random.choice(UA_LIST))
   ```
3. **Proxy Support** (free tier):

   * `page.context().set_http_credentials` for auth proxies.
4. **Randomized Delays & Mouse Movements** (see § 4.2).

---

## 8. Scaling & Concurrency

* **Worker Pool**: spin N workers (where N ≈ RAM / 2 GB) on a single machine.
* **Rate Limiting**: per-domain token buckets to avoid bans.
* **Horizontal Scale**: containerize (`Dockerfile`), deploy to k8s or Fly.io, each pod runs 1–2 workers.

---

## 9. Integrating into a Website

1. **API Endpoints**:

   * `POST /jobs` → enqueue scrape job
   * `GET  /jobs/{id}` → status + partial logs
   * `GET  /jobs/{id}/results` → JSON data

2. **WebSocket/Server-Sent Events** for live log streaming.

3. **Frontend** (React):

   * Job form (URL, login creds)
   * Live logs panel
   * Results table / JSON viewer

4. **Authentication & Access Control**: JWT + role checks.

---

## 10. Putting It All Together

1. **Start your Redis** or RabbitMQ locally.
2. **Launch API server** (`uvicorn main:app`)
3. **Run worker(s)** (`python worker.py`)
4. **Fire up Frontend** (`npm run dev`)
5. **Upload Q2\_K model** under `models/`, configure `LLAMA_MODEL_PATH`.
6. **Scrape** by submitting a job—watch the AI agent “think” via logs, then inspect structured JSON output.

---

With this blueprint, you have **every piece**—from LLM-prompt templates to Playwright execution, selector extraction logic, error resilience, and full web-app integration—to build an Origami-style AI scraping service using the lightweight Q2\_K model on commodity hardware.
