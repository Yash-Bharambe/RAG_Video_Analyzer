"""User-facing explanations for hosted AI errors."""
import httpx


def explain_error(error: Exception) -> str:
    current = error
    seen = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, httpx.HTTPStatusError):
            provider = {"api.mistral.ai": "Mistral", "api.groq.com": "Groq"}.get(current.request.url.host)
            if current.response.status_code == 429 and provider:
                return (
                    f"{provider} free-tier limit reached. This project uses {provider}'s free API tier, "
                    "which limits requests and token usage. Please wait a few minutes before "
                    "trying again. If this continues, check the remaining quota in your "
                    f"{provider} account, or select the other AI provider and run Analyse again."
                )
        current = current.__cause__ or current.__context__
    return f"Processing failed: {error}"
