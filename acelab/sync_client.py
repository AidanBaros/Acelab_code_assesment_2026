"""Synchronous client wrapper around async client."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from ._base import BaseClient
from .client import AsyncAcelab
from .sync_resources import (
    SyncCertificationsResource,
    SyncCompaniesResource,
    SyncMaterialsResource,
    SyncTaxonomyResource,
)


if TYPE_CHECKING:
    from .models import DeduplicateResponse, SearchResponse


class Acelab(BaseClient):
    """Sync client for Acelab Vector Search API.

    Usage::

        client = Acelab(api_key="...")

        # Product search
        results = client.search("quartz countertop")
        print(results.results[0].manufacturer_product_name)

        # Namespaced resources
        materials = client.materials.search("granite")
        certs = client.certifications.search("LEED")
        companies = client.companies.search("Granite Inc")
        taxonomy = client.taxonomy.search("Ceramic Tiling")
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._async_client: AsyncAcelab | None = None
        self._materials: SyncMaterialsResource | None = None
        self._certifications: SyncCertificationsResource | None = None
        self._companies: SyncCompaniesResource | None = None
        self._taxonomy: SyncTaxonomyResource | None = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create a persistent event loop for sync operations."""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise RuntimeError(
                "Cannot use sync client from async context. Use AsyncAcelab instead."
            )
        return self._get_loop().run_until_complete(coro)

    def _ensure_resources(self) -> AsyncAcelab:
        """Lazily create the underlying async client and resource namespaces."""
        if self._async_client is None:
            client = AsyncAcelab(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
            # Manually initialise the httpx client (mirrors __aenter__)
            self._run_async(client.__aenter__())
            self._async_client = client
            self._materials = SyncMaterialsResource(client.materials, self._run_async)
            self._certifications = SyncCertificationsResource(
                client.certifications, self._run_async
            )
            self._companies = SyncCompaniesResource(client.companies, self._run_async)
            self._taxonomy = SyncTaxonomyResource(client.taxonomy, self._run_async)
        return self._async_client

    # -- Resource namespaces -------------------------------------------------

    @property
    def materials(self) -> SyncMaterialsResource:
        """Materials resource (``/api/v1/materials``)."""
        self._ensure_resources()
        assert self._materials is not None
        return self._materials

    @property
    def certifications(self) -> SyncCertificationsResource:
        """Certifications resource (``/api/v1/certifications``)."""
        self._ensure_resources()
        assert self._certifications is not None
        return self._certifications

    @property
    def companies(self) -> SyncCompaniesResource:
        """Companies resource (``/api/v1/companies``)."""
        self._ensure_resources()
        assert self._companies is not None
        return self._companies

    @property
    def taxonomy(self) -> SyncTaxonomyResource:
        """Taxonomy resource (``/api/v1/taxonomy``)."""
        self._ensure_resources()
        assert self._taxonomy is not None
        return self._taxonomy

    # -- Top-level methods ---------------------------------------------------

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> SearchResponse:
        """Search products using semantic similarity."""
        client = self._ensure_resources()

        async def _search() -> SearchResponse:
            return await client.search(query, limit=limit, offset=offset)

        return self._run_async(_search())

    def deduplicate(
        self,
        *,
        name: str,
        supplier: str,
        description: str | None = None,
        attributes: dict[str, str] | None = None,
    ) -> DeduplicateResponse:
        """Find duplicate or similar products."""
        client = self._ensure_resources()

        async def _deduplicate() -> DeduplicateResponse:
            return await client.deduplicate(
                name=name,
                supplier=supplier,
                description=description,
                attributes=attributes,
            )

        return self._run_async(_deduplicate())
