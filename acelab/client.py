"""Async client for the Acelab Vector Search API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from ._base import BaseClient
from .exceptions import AcelabAPIError
from .models import DeduplicateResponse, SearchResponse
from .resources import (
    CertificationsResource,
    CompaniesResource,
    MaterialsResource,
    TaxonomyResource,
)


if TYPE_CHECKING:
    from types import TracebackType


class AsyncAcelab(BaseClient):
    """Async client for Acelab Vector Search API.

    Usage::

        async with AsyncAcelab(api_key="...") as client:
            # Product search
            results = await client.search("quartz countertop")
            print(results.results[0].manufacturer_product_name)

            # Namespaced resources
            materials = await client.materials.search("granite")
            certs = await client.certifications.search("LEED")
            companies = await client.companies.search("Granite Inc")
            taxonomy = await client.taxonomy.search("Ceramic Tiling")
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._client: httpx.AsyncClient | None = None
        # Resource namespaces (initialized when client enters context)
        self._materials: MaterialsResource | None = None
        self._certifications: CertificationsResource | None = None
        self._companies: CompaniesResource | None = None
        self._taxonomy: TaxonomyResource | None = None

    async def __aenter__(self) -> AsyncAcelab:
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._build_headers(),
            timeout=self.timeout,
            follow_redirects=True,
        )
        self._materials = MaterialsResource(self._client)
        self._certifications = CertificationsResource(self._client)
        self._companies = CompaniesResource(self._client)
        self._taxonomy = TaxonomyResource(self._client)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with AsyncAcelab() as client:'")
        return self._client

    # -- Resource namespaces -------------------------------------------------

    @property
    def materials(self) -> MaterialsResource:
        """Materials resource (``/api/v1/materials``)."""
        if self._materials is None:
            raise RuntimeError("Client not initialized. Use 'async with AsyncAcelab() as client:'")
        return self._materials

    @property
    def certifications(self) -> CertificationsResource:
        """Certifications resource (``/api/v1/certifications``)."""
        if self._certifications is None:
            raise RuntimeError("Client not initialized. Use 'async with AsyncAcelab() as client:'")
        return self._certifications

    @property
    def companies(self) -> CompaniesResource:
        """Companies resource (``/api/v1/companies``)."""
        if self._companies is None:
            raise RuntimeError("Client not initialized. Use 'async with AsyncAcelab() as client:'")
        return self._companies

    @property
    def taxonomy(self) -> TaxonomyResource:
        """Taxonomy resource (``/api/v1/taxonomy``)."""
        if self._taxonomy is None:
            raise RuntimeError("Client not initialized. Use 'async with AsyncAcelab() as client:'")
        return self._taxonomy

    # -- Top-level methods ---------------------------------------------------

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> SearchResponse:
        """Search products using semantic similarity.

        Args:
            query: Natural language search query.
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            Typed search response with results, query, and metadata.
        """
        params: dict[str, Any] = {"query": query, "limit": limit, "offset": offset}
        response = await self.client.post("/search/", params=params)
        _raise_for_status(response)
        return SearchResponse.model_validate(response.json())

    async def deduplicate(
        self,
        *,
        name: str,
        supplier: str,
        description: str | None = None,
        attributes: dict[str, str] | None = None,
    ) -> DeduplicateResponse:
        """Find duplicate or similar products.

        Args:
            name: Product name.
            supplier: Supplier name.
            description: Optional product description.
            attributes: Optional additional product attributes.

        Returns:
            Typed deduplication response with candidate matches.
        """
        payload: dict[str, Any] = {"name": name, "supplier": supplier}
        if description is not None:
            payload["description"] = description
        if attributes is not None:
            payload["attributes"] = attributes
        response = await self.client.post("/deduplication/", json=payload)
        _raise_for_status(response)
        return DeduplicateResponse.model_validate(response.json())


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
