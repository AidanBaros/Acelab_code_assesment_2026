class BaseClient:
    """Shared configuration and logic"""

    def __init__(
        self,
        api_key: str | None = None,
        # TODO: point this to production URL when ready
        base_url: str = "http://localhost:8000/api/v1",
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
