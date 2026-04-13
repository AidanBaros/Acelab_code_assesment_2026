import httpx


class AcelabError(Exception):
    """Base exception for Acelab SDK"""


class AcelabAPIError(AcelabError):
    """API request failed"""

    def __init__(self, message: str, response: httpx.Response | None = None) -> None:
        super().__init__(message)
        self.response = response
        self.status_code = response.status_code if response else None
