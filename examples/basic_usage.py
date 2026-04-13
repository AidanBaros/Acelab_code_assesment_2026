"""Basic examples of using the Acelab SDK."""

import os

from dotenv import load_dotenv

load_dotenv()

from acelab import Acelab

client = Acelab(
    api_key=os.getenv("ACELAB_API_KEY"),
    base_url=os.getenv("ACELAB_BASE_URL"),
)


# Product Search
# Semantic search across the full product catalog

results = client.search("porcelain floor tile for commercial spaces", limit=5)

print(f"Found {results.total_results} products for: '{results.query}'\n")
for r in results.results:
    print(f"  {r.manufacturer_product_name}")
    print(f"    Supplier:   {r.supplier_name}")
    print(f"    Score:      {r.similarity_score:.2f}")
    print()


# Material Search
# Search material types (e.g., "vinyl", "quartz", "terrazzo")

materials = client.materials.search("luxury vinyl tile", limit=3)

print(f"Materials matching: '{materials.query}'\n")
for m in materials.results:
    print(f"  {m.display_name or m.name} (score: {m.similarity_score:.2f})")
    if m.notes:
        print(f"    Notes: {m.notes[:100]}...")
    print()


# Certification Search
# Search certifications by name, standard, or concept

certs = client.certifications.search("LEED", limit=3)

print(f"Certifications matching: '{certs.query}'\n")
for c in certs.results:
    print(f"  {c.name}")
    if c.long_name:
        print(f"    Full name: {c.long_name}")
    if c.issuing_body_names:
        print(f"    Issued by:  {', '.join(c.issuing_body_names)}")
    print(f"    Score:      {c.similarity_score:.2f}")
    print()


# Company Search
# Search manufacturers, suppliers, and brands

companies = client.companies.search("Armstrong", limit=3)

print(f"Companies matching: '{companies.query}'\n")
for co in companies.results:
    print(f"  {co.name}")
    if co.long_name:
        print(f"    Full name: {co.long_name}")
    if co.website:
        print(f"    Website:   {co.website}")
    print(f"    Score:     {co.similarity_score:.2f}")
    print()


# Taxonomy Search
# Classify a product into Acelab's taxonomy (uses threshold matching)

taxonomy = client.taxonomy.search(
    product_category_scraped="ceramic floor tile",
    product_description="Large format porcelain tile for high-traffic commercial flooring",
)

print("Taxonomy classification:\n")
if taxonomy.new_taxonomy and taxonomy.new_taxonomy.matched_taxonomy:
    match = taxonomy.new_taxonomy.matched_taxonomy
    print(f"  Matched: {match.display_name or match.name}")
    print(f"  Score:   {match.similarity_score:.2f}")
    print(f"  Status:  {taxonomy.new_taxonomy.match_status}")
else:
    print("  No confident match")
    if taxonomy.new_taxonomy and taxonomy.new_taxonomy.top_candidates:
        print("  Top candidates:")
        for tc in taxonomy.new_taxonomy.top_candidates:
            print(f"    - {tc.display_name or tc.name} ({tc.similarity_score:.2f})")

print()


# Deduplication
# Check if a product already exists in the catalog

dupes = client.deduplicate(
    name="Quartz Countertop - White",
    supplier="Caesarstone",
    description="Premium quartz surface, 3cm thickness",
    attributes={"material": "quartz", "color": "white"},
)

print("Deduplication results:\n")
for d in dupes.candidates:
    label = "LIKELY DUPE" if d.is_likely_duplicate else "similar"
    print(f"  [{label}] {d.manufacturer_product_name}")
    print(f"    Supplier: {d.supplier_name}")
    print(f"    Score:    {d.similarity_score:.2f}")
    print()