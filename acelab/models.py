"""Typed response models for the Acelab SDK."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Product search
# ---------------------------------------------------------------------------


class ProductSearchResult(BaseModel):
    """Individual product search result."""

    product_id: str
    manufacturer_product_name: str
    acelab_name: str | None = None
    acelab_subname: str | None = None
    supplier_name: str | None = None
    status_name: str | None = None
    market_status: str | None = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class SearchResponse(BaseModel):
    """Response from product search."""

    results: list[ProductSearchResult]
    query: str
    total_results: int
    top_k: int


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------


class Material(BaseModel):
    """A material record."""

    id: str
    name: str | None = None
    display_name: str | None = None
    alt_names: str | None = None
    notes: str | None = None


class MaterialSearchResult(BaseModel):
    """Individual material search result with similarity score."""

    id: str
    name: str | None = None
    display_name: str | None = None
    alt_names: str | None = None
    notes: str | None = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class MaterialSearchResponse(BaseModel):
    """Response from material search."""

    results: list[MaterialSearchResult]
    query: str
    total_results: int
    top_k: int


class MaterialListResponse(BaseModel):
    """Paginated list of materials."""

    results: list[Material]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Certifications
# ---------------------------------------------------------------------------


class Certification(BaseModel):
    """A certification record."""

    id: str
    name: str | None = None
    long_name: str | None = None
    description: str | None = None
    tooltip: str | None = None
    acelab_research: str | None = None
    source_url: str | None = None
    url_slug: str | None = None
    legacy_versions: dict[str, object] | list[object] | None = None
    issuing_body_names: list[str | None] | None = None


class CertificationSearchResult(BaseModel):
    """Individual certification search result with similarity score."""

    id: str
    name: str | None = None
    long_name: str | None = None
    description: str | None = None
    tooltip: str | None = None
    source_url: str | None = None
    legacy_versions: dict[str, object] | list[object] | None = None
    issuing_body_names: list[str] | None = None
    status_name: str | None = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class CertificationSearchResponse(BaseModel):
    """Response from certification search."""

    results: list[CertificationSearchResult]
    query: str
    total_results: int
    top_k: int


class CertificationListResponse(BaseModel):
    """Paginated list of certifications."""

    results: list[Certification]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------


class Company(BaseModel):
    """A company record."""

    id: str
    name: str | None = None
    long_name: str | None = None
    website: str | None = None
    domain: str | None = None


class CompanySearchResult(BaseModel):
    """Individual company search result with similarity score."""

    id: str
    name: str | None = None
    long_name: str | None = None
    website: str | None = None
    domain: str | None = None
    status_name: str | None = None
    market_status: str | None = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class CompanySearchResponse(BaseModel):
    """Response from company search."""

    results: list[CompanySearchResult]
    query: str
    total_results: int
    top_k: int


class CompanyListResponse(BaseModel):
    """Paginated list of companies."""

    results: list[Company]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Taxonomy
# ---------------------------------------------------------------------------


class Taxonomy(BaseModel):
    """A taxonomy record."""

    id: str
    name: str | None = None
    display_name: str | None = None
    alt_names: list[str] | str | None = None
    description: str | None = None
    guide: str | None = None
    tooltip: str | None = None
    url_slug: str | None = None
    masterformat_code: str | None = None


class TaxonomySearchResult(BaseModel):
    """Individual taxonomy search result with similarity score."""

    id: str
    name: str | None = None
    display_name: str | None = None
    taxonomy_type_name: str | None = None
    alt_names: list[str] | str | None = None
    description: str | None = None
    guide: str | None = None
    tooltip: str | None = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    masterformat_code: str | None = None


class TaxonomyMatchResult(BaseModel):
    """Single taxonomy type match result (old or new)."""

    match_status: str
    matched_taxonomy: TaxonomySearchResult | None = None
    top_candidates: list[TaxonomySearchResult]
    threshold: float = 0.75


class TaxonomySearchResponse(BaseModel):
    """Response from taxonomy search with dual old/new taxonomy matching."""

    old_taxonomy: TaxonomyMatchResult
    new_taxonomy: TaxonomyMatchResult
    query_input: dict[str, str]


class TaxonomyListResponse(BaseModel):
    """Paginated list of taxonomies."""

    results: list[Taxonomy]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


class DeduplicateCandidate(BaseModel):
    """A candidate duplicate product."""

    product_id: str
    manufacturer_product_name: str
    acelab_name: str | None = None
    acelab_subname: str | None = None
    supplier_name: str | None = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    is_likely_duplicate: bool


class DeduplicateResponse(BaseModel):
    """Response from deduplication."""

    candidates: list[DeduplicateCandidate]
