"""Acelab Vector Search SDK"""

from .client import AsyncAcelab
from .exceptions import AcelabAPIError, AcelabError
from .models import (
    Certification,
    CertificationListResponse,
    CertificationSearchResponse,
    CertificationSearchResult,
    Company,
    CompanyListResponse,
    CompanySearchResponse,
    CompanySearchResult,
    DeduplicateCandidate,
    DeduplicateResponse,
    Material,
    MaterialListResponse,
    MaterialSearchResponse,
    MaterialSearchResult,
    ProductSearchResult,
    SearchResponse,
    Taxonomy,
    TaxonomyListResponse,
    TaxonomyMatchResult,
    TaxonomySearchResponse,
    TaxonomySearchResult,
)
from .sync_client import Acelab


__version__ = "0.1.0"

__all__ = [
    "Acelab",
    "AcelabAPIError",
    "AcelabError",
    "AsyncAcelab",
    "Certification",
    "CertificationListResponse",
    "CertificationSearchResponse",
    "CertificationSearchResult",
    "Company",
    "CompanyListResponse",
    "CompanySearchResponse",
    "CompanySearchResult",
    "DeduplicateCandidate",
    "DeduplicateResponse",
    "Material",
    "MaterialListResponse",
    "MaterialSearchResponse",
    "MaterialSearchResult",
    "ProductSearchResult",
    "SearchResponse",
    "Taxonomy",
    "TaxonomyListResponse",
    "TaxonomyMatchResult",
    "TaxonomySearchResponse",
    "TaxonomySearchResult",
]
