"""Material Recommendation Agent — Acelab Take-Home."""

import json
import os
import sys
from collections import defaultdict

from dotenv import load_dotenv
from openai import OpenAI

from acelab import Acelab

load_dotenv()

acelab = Acelab(
    api_key=os.getenv("ACELAB_API_KEY"),
    base_url=os.getenv("ACELAB_BASE_URL"),
)

llm = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

MODEL = "openai/gpt-4o"
SCORE_THRESHOLD = 0.65       # Filter out low-confidence results before synthesis
FALLBACK_THRESHOLD = 0.60    # Looser threshold used in the fallback pass
MIN_PRODUCTS = 5             # Minimum products required before synthesis


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Semantic search across the full Acelab product catalog. "
                "Use for finding specific products by material type, use case, or performance criteria."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "limit": {"type": "integer", "default": 8, "description": "Max results (default 8)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_materials",
            "description": (
                "Search Acelab's material type taxonomy (e.g., 'vinyl', 'quartz', 'terrazzo', 'rubber'). "
                "Use to identify which material categories are most relevant before searching products."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Material type or concept"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_certifications",
            "description": (
                "Search certifications and sustainability standards (e.g., 'LEED', 'FSC', 'FloorScore', "
                "'Cradle to Cradle', 'antimicrobial', 'Red List Free'). "
                "Use to identify which certs are relevant to the project's requirements."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Certification name or concept"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_companies",
            "description": (
                "Search manufacturers and suppliers. "
                "Use to find reputable brands known for specific material types or performance standards."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Company or brand name, or manufacturer type"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_taxonomy",
            "description": (
                "Classify a product or space into Acelab's product taxonomy. "
                "Use early to identify the correct product categories for this project, "
                "which then informs more targeted product searches."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Product category or space type to classify (e.g., 'commercial flooring', 'wall cladding')",
                    },
                    "description": {
                        "type": "string",
                        "description": "Additional context about the use case",
                        "default": "",
                    },
                },
                "required": ["category"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Phase 1: Planning
# ---------------------------------------------------------------------------

PLANNING_PROMPT = """\
You are an expert building materials consultant helping architects find the right products.

Given a project description, produce a structured search plan as JSON.
Identify every dimension that needs to be searched — be thorough and specific.

Return a JSON object with this exact structure:
{
  "project_summary": "one sentence summary of the project",
  "space_type": "type of space (e.g., hospital corridor, office lobby)",
  "key_requirements": ["list", "of", "requirements"],
  "searches": [
    {"tool": "search_taxonomy", "query": "...", "purpose": "classify the space type"},
    {"tool": "search_materials", "query": "...", "purpose": "..."},
    {"tool": "search_certifications", "query": "...", "purpose": "..."},
    {"tool": "search_products", "query": "...", "purpose": "..."},
    {"tool": "search_companies", "query": "...", "purpose": "..."}
  ]
}

Rules for the searches list:
- Include at least 8 searches total
- Search each material category separately (e.g., separate queries for "rubber flooring", "LVT", "porcelain tile")
- Search each certification separately (e.g., "LEED Silver", "infection control standard", "antimicrobial")
- Search manufacturers relevant to the material types
- Search product use cases specifically (e.g., "high-traffic hospital corridor flooring")
- Always start with a taxonomy search to classify the space
- Do NOT combine multiple topics into one query — specific queries get better results\
"""


def plan_searches(user_query: str) -> dict:
    """Phase 1: Ask the LLM to produce a structured search plan before any tool calls."""
    response = llm.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PLANNING_PROMPT},
            {"role": "user", "content": user_query},
        ],
        response_format={"type": "json_object"},
        temperature=0,  # Planning is pure reasoning — no creativity needed
    )
    return json.loads(response.choices[0].message.content)


# ---------------------------------------------------------------------------
# Phase 2: Tool execution
# ---------------------------------------------------------------------------

def execute_tool(name: str, args: dict) -> tuple[str, list[dict]]:
    """
    Dispatch a tool call to the Acelab SDK.
    Returns (json_string_for_llm, list_of_raw_result_dicts).
    Raw results are used for deduplication and synthesis.
    """
    raw = []
    try:
        if name == "search_products":
            r = acelab.search(args["query"], limit=args.get("limit", 8))
            products = [
                {
                    "name": p.manufacturer_product_name,
                    "subname": p.acelab_subname,
                    "supplier": p.supplier_name,
                    "score": round(p.similarity_score, 3),
                    "market_status": p.market_status,
                    "search_query": args["query"],
                }
                for p in r.results
                if p.similarity_score >= SCORE_THRESHOLD
            ]
            raw = products
            return json.dumps({"query": r.query, "products": products}), raw

        elif name == "search_materials":
            r = acelab.materials.search(args["query"], limit=args.get("limit", 5))
            materials = [
                {
                    "name": m.display_name or m.name,
                    "score": round(m.similarity_score, 3),
                    "notes": m.notes,
                }
                for m in r.results
                if m.similarity_score >= SCORE_THRESHOLD
            ]
            raw = materials
            return json.dumps({"query": r.query, "materials": materials}), raw

        elif name == "search_certifications":
            r = acelab.certifications.search(args["query"], limit=args.get("limit", 5))
            certs = [
                {
                    "name": c.name,
                    "full_name": c.long_name,
                    "description": c.description,
                    "issued_by": c.issuing_body_names,
                    "score": round(c.similarity_score, 3),
                }
                for c in r.results
                if c.similarity_score >= SCORE_THRESHOLD
            ]
            raw = certs
            return json.dumps({"query": r.query, "certifications": certs}), raw

        elif name == "search_companies":
            r = acelab.companies.search(args["query"], limit=args.get("limit", 5))
            companies = [
                {
                    "name": co.name,
                    "website": co.website,
                    "score": round(co.similarity_score, 3),
                }
                for co in r.results
                if co.similarity_score >= SCORE_THRESHOLD
            ]
            raw = companies
            return json.dumps({"query": r.query, "companies": companies}), raw

        elif name == "search_taxonomy":
            r = acelab.taxonomy.search(
                args["category"],
                product_description=args.get("description", ""),
            )
            result = {}
            if r.new_taxonomy and r.new_taxonomy.matched_taxonomy:
                m = r.new_taxonomy.matched_taxonomy
                result = {
                    "matched_category": m.display_name or m.name,
                    "score": round(m.similarity_score, 3),
                    "status": r.new_taxonomy.match_status,
                    "description": m.description,
                    "guide": m.guide,
                }
            elif r.new_taxonomy and r.new_taxonomy.top_candidates:
                result = {
                    "matched_category": None,
                    "top_candidates": [
                        {"name": c.display_name or c.name, "score": round(c.similarity_score, 3)}
                        for c in r.new_taxonomy.top_candidates
                    ],
                }
            raw = [result] if result else []
            return json.dumps(result), raw

        else:
            return json.dumps({"error": f"Unknown tool: {name}"}), []

    except Exception as e:
        return json.dumps({"error": str(e)}), []


def run_searches(plan: dict, user_query: str, on_progress=None) -> tuple[list[dict], dict]:
    """
    Phase 2: Execute the planned searches via the tool-calling loop.
    The LLM can also make additional searches it deems necessary.
    Returns (messages_history, aggregated_results).
    """
    SEARCH_PROMPT = f"""\
You are executing a material search for an architect. Here is the search plan:

Project: {plan.get('project_summary', '')}
Requirements: {', '.join(plan.get('key_requirements', []))}

Execute EVERY search in the plan below — all of them, in order.
Do NOT skip any. Do NOT add extra searches beyond the plan.
Do NOT attempt to synthesize or write recommendations — just execute the searches.\
"""

    messages = [
        {"role": "system", "content": SEARCH_PROMPT},
        {
            "role": "user",
            "content": (
                f"Execute these searches:\n{json.dumps(plan.get('searches', []), indent=2)}\n\n"
                f"Original query: {user_query}"
            ),
        },
    ]

    # Aggregate raw results for deduplication and synthesis
    aggregated = {
        "products": defaultdict(lambda: {"score": 0, "appearances": 0, "queries": [], "supplier": None, "subname": None, "market_status": None}),
        "materials": [],
        "certifications": [],
        "companies": [],
        "taxonomy": [],
        "supplier_websites": {},  # supplier_name -> website URL
    }

    while True:
        response = llm.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0,  # Search execution is mechanical — deterministic tool dispatch
        )

        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            query_text = args.get("query") or args.get("category", "")
            if on_progress:
                on_progress("tool", f"{name}:{query_text}")
            else:
                print(f"  [{name}] {query_text}")
            result_str, raw = execute_tool(name, args)

            # Aggregate results
            if name == "search_products":
                for p in raw:
                    key = p["name"]
                    aggregated["products"][key]["score"] = max(
                        aggregated["products"][key]["score"], p["score"]
                    )
                    aggregated["products"][key]["appearances"] += 1
                    aggregated["products"][key]["queries"].append(p["search_query"])
                    aggregated["products"][key]["supplier"] = p.get("supplier")
                    if p.get("subname"):
                        aggregated["products"][key]["subname"] = p["subname"]
                    if p.get("market_status"):
                        aggregated["products"][key]["market_status"] = p["market_status"]
            elif name == "search_materials":
                aggregated["materials"].extend(raw)
            elif name == "search_certifications":
                aggregated["certifications"].extend(raw)
            elif name == "search_companies":
                for co in raw:
                    if co.get("name") and co.get("website"):
                        aggregated["supplier_websites"][co["name"]] = co["website"]
                aggregated["companies"].extend(raw)
            elif name == "search_taxonomy":
                aggregated["taxonomy"].extend(raw)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str,
            })

    return messages, aggregated


# ---------------------------------------------------------------------------
# Phase 2b: Fallback search (if not enough products found)
# ---------------------------------------------------------------------------

FALLBACK_PROMPT = """\
A material search for an architect returned fewer products than needed.
Given the original project requirements and the searches already run, suggest 6-8 NEW product search queries
that take a broader or different angle to surface more matching products.

Return a JSON object:
{
  "queries": ["query 1", "query 2", ...]
}

Rules:
- Only include search_products queries (not materials/certifications/companies)
- Do NOT repeat queries that were already run
- Try broader material categories, adjacent product types, or different terminology
- Still stay relevant to the project requirements\
"""


def run_fallback_searches(
    user_query: str,
    plan: dict,
    aggregated: dict,
    already_run: list[str],
    on_progress=None,
) -> None:
    """
    Phase 2b: Generate and run additional product searches when MIN_PRODUCTS isn't met.
    Mutates `aggregated` in place. Uses a looser score threshold.
    """
    context = {
        "original_query": user_query,
        "project_requirements": plan.get("key_requirements", []),
        "searches_already_run": already_run,
        "products_found_so_far": list(aggregated["products"].keys()),
    }

    response = llm.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": FALLBACK_PROMPT},
            {"role": "user", "content": json.dumps(context)},
        ],
        response_format={"type": "json_object"},
        temperature=0,  # Fallback query generation should be deterministic
    )
    new_queries = json.loads(response.choices[0].message.content).get("queries", [])

    for query in new_queries:
        if on_progress:
            on_progress("tool", f"search_products:{query}")
        else:
            print(f"  [fallback] {query}")

        try:
            r = acelab.search(query, limit=10)
            for p in r.results:
                if p.similarity_score < FALLBACK_THRESHOLD:
                    continue
                key = p.manufacturer_product_name
                aggregated["products"][key]["score"] = max(
                    aggregated["products"][key]["score"],
                    round(p.similarity_score, 3),
                )
                aggregated["products"][key]["appearances"] += 1
                aggregated["products"][key]["queries"].append(query)
                aggregated["products"][key]["supplier"] = p.supplier_name
                if p.acelab_subname:
                    aggregated["products"][key]["subname"] = p.acelab_subname
                if p.market_status:
                    aggregated["products"][key]["market_status"] = p.market_status
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Phase 3: Synthesis
# ---------------------------------------------------------------------------

SYNTHESIS_PROMPT = """\
You are an expert building materials consultant writing recommendations for an architect.

You have been given the results of multiple targeted searches. Each product includes:
- `name`: product name
- `subname`: product type/subcategory (e.g. "Sheet Flooring", "Interlocking Tiles Floor")
- `supplier`: manufacturer name
- `supplier_website`: manufacturer website if available (use this to create a link)
- `market_status`: e.g. "Current Product"
- `best_score`: semantic similarity to the queries (0–1)
- `appearances`: how many separate searches this product appeared in

Produce exactly 5 ranked recommendations (or more if the data supports it). For each, use this exact markdown format:

### 1. [Product Name](https://supplier_website) by Supplier Name
*(only include the link if supplier_website is provided; otherwise just write the name)*

**Type:** subname (if available)
**Manufacturer:** Supplier Name — [supplier_website](https://supplier_website) (if available)

**Why it fits:** Specific explanation tying the product to the project's requirements, certifications, aesthetics, and budget. Reference the relevant certifications from the search data by name.

**Technical notes:** Mention product type, relevant material properties, and market status.

**Trade-offs:** Honest limitations.

**Match confidence:** X/10 — justify based on appearances count and similarity score.

---

Rules:
- Only use URLs that appear in the `supplier_website` field — never guess or invent URLs
- Products with more appearances are higher confidence — factor this into ranking
- Reference real certification names from the `relevant_certifications` data
- Write for an architect — professional, specific, no marketing language\
"""

SYNTHESIS_PROMPT_DEV = """\
You are an expert building materials consultant writing recommendations for an architect.

You have been given the results of multiple targeted searches. Each product includes:
- `name`: product name
- `subname`: product type/subcategory (e.g. "Sheet Flooring", "Interlocking Tiles Floor")
- `supplier`: manufacturer name
- `supplier_website`: manufacturer website if available (use this to create a link)
- `market_status`: e.g. "Current Product"
- `best_score`: semantic similarity to the queries (0–1)
- `appearances`: how many separate searches this product appeared in

Produce exactly 5 ranked recommendations (or more if the data supports it). For each, use this exact markdown format:

### 1. [Product Name](https://supplier_website) by Supplier Name
*(only include the link if supplier_website is provided; otherwise just write the name)*

**Type:** subname (if available)
**Manufacturer:** Supplier Name — [supplier_website](https://supplier_website) (if available)

**Why it fits:** Specific explanation tying the product to the project's requirements, certifications, aesthetics, and budget. Reference the relevant certifications from the search data by name.

**Trade-offs:** Honest limitations.

---

Rules:
- Only use URLs that appear in the `supplier_website` field — never guess or invent URLs
- Products with more appearances are higher confidence — factor this into ranking
- Reference real certification names from the `relevant_certifications` data
- Write for an architect — professional, specific, no marketing language
- Do NOT include any confidence scores, similarity scores, appearance counts, or other numerical metrics
- Do NOT include a "Technical notes" section or any market status information\
"""


def synthesize(user_query: str, plan: dict, aggregated: dict, dev_mode: bool = False) -> str:
    """Phase 3: Dedicated synthesis call with all gathered data."""

    # Rank products by a combined score: best similarity * log(appearances+1)
    import math
    supplier_websites = aggregated.get("supplier_websites", {})
    ranked_products = sorted(
        [
            {
                "name": name,
                "subname": data.get("subname"),
                "supplier": data["supplier"],
                "supplier_website": supplier_websites.get(data["supplier"]) if data["supplier"] else None,
                "market_status": data.get("market_status"),
                "best_score": data["score"],
                "appearances": data["appearances"],
                "found_in_searches": data["queries"],
                "combined_rank": round(data["score"] * math.log(data["appearances"] + 1.5), 3),
            }
            for name, data in aggregated["products"].items()
        ],
        key=lambda x: x["combined_rank"],
        reverse=True,
    )

    # Deduplicate certs and materials by name
    seen_certs = set()
    unique_certs = []
    for c in aggregated["certifications"]:
        if c.get("name") and c["name"] not in seen_certs:
            seen_certs.add(c["name"])
            unique_certs.append(c)

    seen_materials = set()
    unique_materials = []
    for m in aggregated["materials"]:
        if m.get("name") and m["name"] not in seen_materials:
            seen_materials.add(m["name"])
            unique_materials.append(m)

    synthesis_data = {
        "original_query": user_query,
        "project_summary": plan.get("project_summary"),
        "key_requirements": plan.get("key_requirements", []),
        "top_products": ranked_products[:20],  # Top 20 for the model to reason over (ensures 5+ recommendations)
        "relevant_certifications": unique_certs,
        "relevant_materials": unique_materials,
        "relevant_companies": aggregated["companies"][:10],
        "taxonomy_classification": aggregated["taxonomy"],
    }

    prompt = SYNTHESIS_PROMPT_DEV if dev_mode else SYNTHESIS_PROMPT
    response = llm.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Search data:\n{json.dumps(synthesis_data, indent=2)}",
            },
        ],
        temperature=0.2,  # Low but not zero — synthesis should read naturally, not robotically
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Main agent runner
# ---------------------------------------------------------------------------

def run_agent(user_query: str, on_progress=None, dev_mode: bool = False) -> str:
    """Run the three-phase material recommendation agent."""

    def emit(event_type: str, message: str) -> None:
        if on_progress:
            on_progress(event_type, message)
        else:
            print(message)

    emit("phase", "Planning searches...")
    plan = plan_searches(user_query)
    emit("plan", json.dumps({
        "summary": plan.get("project_summary", ""),
        "requirements": plan.get("key_requirements", []),
        "search_count": len(plan.get("searches", [])),
    }))

    emit("phase", "Executing searches...")
    _, aggregated = run_searches(plan, user_query, on_progress=on_progress)

    # If not enough products found, run a fallback pass with broader queries
    if len(aggregated["products"]) < MIN_PRODUCTS:
        already_run = [s["query"] for s in plan.get("searches", []) if s.get("tool") == "search_products"]
        emit("phase", f"Only {len(aggregated['products'])} products found — expanding search...")
        run_fallback_searches(user_query, plan, aggregated, already_run, on_progress=on_progress)

    # Fetch websites for any product suppliers not already captured from company searches
    missing = {
        data["supplier"]
        for data in aggregated["products"].values()
        if data["supplier"] and data["supplier"] not in aggregated["supplier_websites"]
    }
    for supplier_name in missing:
        try:
            r = acelab.companies.search(supplier_name, limit=1)
            if r.results and r.results[0].website:
                aggregated["supplier_websites"][supplier_name] = r.results[0].website
        except Exception:
            pass

    emit("phase", f"Found {len(aggregated['products'])} products across all searches — synthesizing...")

    result = synthesize(user_query, plan, aggregated, dev_mode=dev_mode)
    return result


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    print("Acelab Material Recommendation Agent")
    print("=" * 40)

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Query: {query}")
    else:
        query = input("Describe your project: ").strip()
        if not query:
            print("No query provided.")
            sys.exit(1)

    result = run_agent(query)

    print("\n" + "=" * 40)
    print("RECOMMENDATIONS")
    print("=" * 40 + "\n")
    print(result)


if __name__ == "__main__":
    main()
