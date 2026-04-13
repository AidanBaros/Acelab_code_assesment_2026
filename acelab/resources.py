"""Async resource namespaces for the Acelab SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .exceptions import AcelabAPIError
from .models import (
    Certification,
    CertificationListResponse,
    CertificationSearchResponse,
    Company,
    CompanyListResponse,
    CompanySearchResponse,
    Material,
    MaterialListResponse,
    MaterialSearchResponse,
    Taxonomy,
    TaxonomyListResponse,
    TaxonomySearchResponse,
)


if TYPE_CHECKING:
    import httpx


def _raise_for_status(response: httpx.Response) -> None:
    """Raise AcelabAPIError on non-2xx responses."""
    if response.is_success:
        return
    try:
        detail = response.json().get("detail", response.text)
    except Exception:
        detail = response.text
    raise AcelabAPIError(
        f"HTTP {response.status_code}: {detail}",
        response=response,
    )


class MaterialsResource:
    """Async resource for /api/v1/materials endpoints."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> MaterialSearchResponse:
        """Search materials using semantic similarity."""
        params: dict[str, Any] = {"query": query, "limit": limit, "offset": offset}
        response = await self._client.get("/materials/search", params=params)
        _raise_for_status(response)
        return MaterialSearchResponse.model_validate(response.json())

    async def list(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> MaterialListResponse:
        """List materials with pagination."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        response = await self._client.get("/materials/", params=params)
        _raise_for_status(response)
        return MaterialListResponse.model_validate(response.json())

    async def get(self, material_id: str) -> Material | None:
        """Get a material by ID."""
        response = await self._client.get(f"/materials/{material_id}")
        _raise_for_status(response)
        data = response.json()
        if data is None:
            return None
        return Material.model_validate(data)


class CertificationsResource:
    """Async resource for /api/v1/certifications endpoints."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
        issuing_body: str | None = None,
        legacy_version: str | None = None,
    ) -> CertificationSearchResponse:
        """Search certifications using semantic similarity."""
        params: dict[str, Any] = {"query": query, "limit": limit, "offset": offset}
        if issuing_body is not None:
            params["issuing_body"] = issuing_body
        if legacy_version is not None:
            params["legacy_version"] = legacy_version
        response = await self._client.get("/certifications/search", params=params)
        _raise_for_status(response)
        return CertificationSearchResponse.model_validate(response.json())

    async def list(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> CertificationListResponse:
        """List certifications with pagination."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        response = await self._client.get("/certifications/", params=params)
        _raise_for_status(response)
        return CertificationListResponse.model_validate(response.json())

    async def get(self, certification_id: str) -> Certification | None:
        """Get a certification by ID."""
        response = await self._client.get(f"/certifications/{certification_id}")
        _raise_for_status(response)
        data = response.json()
        if data is None:
            return None
        return Certification.model_validate(data)


class CompaniesResource:
    """Async resource for /api/v1/companies endpoints."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> CompanySearchResponse:
        """Search companies using semantic similarity."""
        params: dict[str, Any] = {"query": query, "limit": limit, "offset": offset}
        response = await self._client.get("/companies/search", params=params)
        _raise_for_status(response)
        return CompanySearchResponse.model_validate(response.json())

    async def list(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> CompanyListResponse:
        """List companies with pagination."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        response = await self._client.get("/companies/", params=params)
        _raise_for_status(response)
        return CompanyListResponse.model_validate(response.json())

    async def get(self, company_id: str) -> Company | None:
        """Get a company by ID."""
        response = await self._client.get(f"/companies/{company_id}")
        _raise_for_status(response)
        data = response.json()
        if data is None:
            return None
        return Company.model_validate(data)


class TaxonomyResource:
    """Async resource for /api/v1/taxonomy endpoints."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def search(
        self,
        product_category_scraped: str,
        *,
        product_description: str = "",
        threshold: float | None = None,
        applicable_to_products: bool | None = True,
        limit: int = 10,
        offset: int = 0,
    ) -> TaxonomySearchResponse:
        """Search taxonomies using semantic similarity with dual old/new matching.

        Args:
            product_category_scraped: Product category as scraped from source.
            product_description: Optional product description for better matching.
            threshold: Minimum similarity score for MATCHED status (default: server-side 0.75).
            applicable_to_products: Filter by product-applicable taxonomies.
                True (default) = only product-applicable. False = only non-applicable.
                None = search all taxonomies.
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            Dual taxonomy response with old_taxonomy and new_taxonomy match results.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        payload: dict[str, Any] = {
            "product_category_scraped": product_category_scraped,
            "product_description": product_description,
        }
        if threshold is not None:
            payload["threshold"] = threshold
        if applicable_to_products is not None:
            payload["applicable_to_products"] = applicable_to_products
        response = await self._client.post("/taxonomy/search", json=payload, params=params)
        _raise_for_status(response)
        return TaxonomySearchResponse.model_validate(response.json())

    async def list(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> TaxonomyListResponse:
        """List taxonomies with pagination."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        response = await self._client.get("/taxonomy/", params=params)
        _raise_for_status(response)
        return TaxonomyListResponse.model_validate(response.json())

    async def get(self, taxonomy_id: str) -> Taxonomy | None:
        """Get a taxonomy by ID."""
        response = await self._client.get(f"/taxonomy/{taxonomy_id}")
        _raise_for_status(response)
        data = response.json()
        if data is None:
            return None
        return Taxonomy.model_validate(data)
