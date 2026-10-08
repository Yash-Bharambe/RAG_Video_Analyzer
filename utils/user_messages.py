"""User-facing explanations for hosted AI errors."""
import httpx


def explain_error(error: Exception) -> str:
    current = error
    seen = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, httpx.HTTPStatusError):
            if current.response.status_code == 429 and current.request.url.host == "api.mistral.ai":
                return (
                    "Mistral free-tier limit reached. This project uses Mistral's free API tier, "
                    "which limits requests and token usage. Please wait a few minutes before "
                    "trying again. If this continues, check the remaining quota in your "
                    "Mistral account."
                )
        current = current.__cause__ or current.__context__
    return f"Processing failed: {error}"
