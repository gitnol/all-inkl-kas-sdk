class KasApiError(Exception):
    """Raised when the KAS API returns an error or fault."""
    pass


class KasAuthError(KasApiError):
    """Raised when authentication fails or credentials are missing."""
    pass


class KasConnectionError(KasApiError):
    """Raised when the HTTP request to the KAS API fails."""
    pass
