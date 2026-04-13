"""Sync resource namespaces for the Acelab SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
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
    from .resources import (
        CertificationsResource,
        CompaniesResource,
        MaterialsResource,
        TaxonomyResource,
    )


# Type alias for the async-to-sync runner function.
type RunAsync = Any  # Callable[[Coroutine], T]


class SyncMaterialsResource:
    """Sync wrapper around MaterialsResource."""

    def __init__(self, async_resource: MaterialsResource, run: RunAsync) -> None:
        self._async = async_resource
        self._run = run

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> MaterialSearchResponse:
        """Search materials using semantic similarity."""
        return self._run(self._async.search(query, limit=limit, offset=offset))

    def list(self, *, limit: int = 10, offset: int = 0) -> MaterialListResponse:
        """List materials with pagination."""
        return self._run(self._async.list(limit=limit, offset=offset))

    def get(self, material_id: str) -> Material | None:
        """Get a material by ID."""
        return self._run(self._async.get(material_id))


class SyncCertificationsResource:
    """Sync wrapper around CertificationsResource."""

    def __init__(self, async_resource: CertificationsResource, run: RunAsync) -> None:
        self._async = async_resource
        self._run = run

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
        issuing_body: str | None = None,
        legacy_version: str | None = None,
    ) -> CertificationSearchResponse:
        """Search certifications using semantic similarity."""
        return self._run(
            self._async.search(
                query,
                limit=limit,
                offset=offset,
                issuing_body=issuing_body,
                legacy_version=legacy_version,
            )
        )

    def list(self, *, limit: int = 10, offset: int = 0) -> CertificationListResponse:
        """List certifications with pagination."""
        return self._run(self._async.list(limit=limit, offset=offset))

    def get(self, certification_id: str) -> Certification | None:
        """Get a certification by ID."""
        return self._run(self._async.get(certification_id))


class SyncCompaniesResource:
    """Sync wrapper around CompaniesResource."""

    def __init__(self, async_resource: CompaniesResource, run: RunAsync) -> None:
        self._async = async_resource
        self._run = run

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> CompanySearchResponse:
        """Search companies using semantic similarity."""
        return self._run(self._async.search(query, limit=limit, offset=offset))

    def list(self, *, limit: int = 10, offset: int = 0) -> CompanyListResponse:
        """List companies with pagination."""
        return self._run(self._async.list(limit=limit, offset=offset))

    def get(self, company_id: str) -> Company | None:
        """Get a company by ID."""
        return self._run(self._async.get(company_id))


class SyncTaxonomyResource:
    """Sync wrapper around TaxonomyResource."""

    def __init__(self, async_resource: TaxonomyResource, run: RunAsync) -> None:
        self._async = async_resource
        self._run = run

    def search(
        self,
        product_category_scraped: str,
        *,
        product_description: str = "",
        threshold: float | None = None,
        applicable_to_products: bool | None = True,
        limit: int = 10,
        offset: int = 0,
    ) -> TaxonomySearchResponse:
        """Search taxonomies using semantic similarity with dual old/new matching."""
        return self._run(
            self._async.search(
                product_category_scraped,
                product_description=product_description,
                threshold=threshold,
                applicable_to_products=applicable_to_products,
                limit=limit,
                offset=offset,
            )
        )

    def list(self, *, limit: int = 10, offset: int = 0) -> TaxonomyListResponse:
        """List taxonomies with pagination."""
        return self._run(self._async.list(limit=limit, offset=offset))

    def get(self, taxonomy_id: str) -> Taxonomy | None:
        """Get a taxonomy by ID."""
        return self._run(self._async.get(taxonomy_id))
