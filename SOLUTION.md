# Solution

## How to Run

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
# 1. Copy env and fill in your keys
cp .env.example .env

# 2. Install dependencies
uv sync

# 3. Start the web server
uv run python app.py
```

Then open [http://localhost:8000](http://localhost:8000) in your browser (Does not work in Safari. If you have an issue with it loading use Chrome).

**Flags:**

```bash
# Default — full output including match confidence, technical notes, and scores
uv run python app.py

# Dev mode — clean user-facing output, no technical stats shown
uv run python app.py --dev
```

**CLI (optional):**

```bash
# Interactive prompt
uv run python agent.py

# Pass query directly
uv run python agent.py "High-traffic hospital corridor, LEED Silver, infection control, mid-range budget"
```

---

## Approach and Key Design Decisions

### Three-phase agent architecture

The agent is split into three explicit phases rather than a single prompt-to-answer loop:

**Phase 1 — Plan:** Before making any API calls, the LLM receives the user's query and produces a structured JSON search plan: a project summary, key requirements, and a list of 10–15 specific searches to run. This forces full decomposition upfront and keeps the plan consistent across runs.

**Phase 2 — Search:** The agent executes every search in the plan against the Acelab SDK — materials, certifications, companies, taxonomy, and products — using tool calling. Results are aggregated into a single deduplicated product pool. Each product tracks its best similarity score and how many separate searches it appeared in. If fewer than 5 products are found above the confidence threshold, a fallback pass asks the LLM for broader queries and reruns with a slightly looser threshold.

**Phase 3 — Synthesize:** A dedicated LLM call receives the pre-ranked product data and writes the final recommendations. This separation means the synthesis model is reasoning over clean, structured data — not raw tool outputs.

### Reducing variance

All LLM calls involved in planning and search execution use `temperature=0`. The search prompt explicitly instructs the model to execute the plan as written with no additions, preventing it from improvising different searches each run. Synthesis uses `temperature=0.2` to keep the prose readable while maintaining consistent ranking.

### Product ranking

Products are ranked by a combined score: `best_similarity_score × log(appearances + 1.5)`. A product that appeared in three different searches with a score of 0.75 ranks above one that scored 0.80 in a single search. This rewards cross-query signal over single-query luck.

### Links via company lookup

The Acelab product search API doesn't return supplier URLs. After the search phase, the agent maps every product's supplier name to a website by querying the companies endpoint. These are attached to each product before synthesis, so the LLM can produce real, verifiable links. The synthesis prompt explicitly forbids inventing URLs.

### Interface

The web UI uses Server-Sent Events (SSE) to stream progress to the browser in real time — users see each search as it fires rather than staring at a loading state. Each search is a new card that stays on screen, so users can compare results from different queries side by side. The search bar is sticky and always available.

---

## What I'd Improve with More Time

**Smarter ranking with product detail enrichment.** The API returns limited product metadata. With more time I'd investigate whether additional endpoints or fields exist to pull in actual spec sheets, product dimensions, material certifications at the product level (rather than inferring them), and pricing tiers. The current ranking is a reasonable proxy but it's working from search signal, not ground truth.

**Caching the planning step.** For similar or repeated queries, the planning phase produces nearly identical search plans. A lightweight cache keyed on a normalized query hash would cut latency significantly for common use cases.

**Better fallback strategy.** The current fallback generates broader queries when fewer than 5 products are found. A more principled approach would analyze *why* results are sparse — wrong material category, overly specific certification query, niche product type — and adjust accordingly.

**Streaming recommendations.** Currently the synthesis result arrives all at once after a ~10s wait. Streaming the synthesis token-by-token would make the UI feel much more responsive.

**Persistent search history.** Right now each search is independent. Storing previous searches would let the agent learn which queries tend to surface high-quality results for a given project type, and let users return to prior sessions.
