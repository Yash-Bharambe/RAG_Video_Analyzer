FROM node:22-bookworm-slim AS javascript
FROM python:3.11-slim-bookworm

COPY --from=javascript /usr/local/bin/node /usr/local/bin/node
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY Requirements.txt /app/Requirements.txt
RUN uv pip install --system --no-cache torch torchaudio --index-url https://download.pytorch.org/whl/cpu \
    && uv pip install --system --no-cache -r Requirements.txt

RUN useradd --create-home --uid 1000 user && chown user:user /app
USER user
ENV HOME=/home/user \
    PYTHONUNBUFFERED=1 \
    LLM_PROVIDER=mistral \
    MISTRAL_MODEL=mistral-small-2603 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
COPY --chown=user:user . /app
EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
