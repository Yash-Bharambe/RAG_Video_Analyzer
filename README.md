---
title: RAG Video Analyzer
emoji: 🎬
colorFrom: purple
colorTo: cyan
sdk: docker
app_port: 8501
pinned: false
license: mit
short_description: Transcribe, summarize & chat with YouTube videos or audio
---

# 🎬 RAG Video Analyzer

**Transcribe · Summarise · Chat with your meetings and videos using AI.**

## Features
- 🔗 Paste a YouTube URL or upload a local audio/video file
- 🎙️ Automatic transcription using OpenAI Whisper (runs locally — no API cost)
- 📋 AI-powered summary, title generation, action items, key decisions & open questions
- 🤖 Chat with the transcript using a RAG (Retrieval-Augmented Generation) pipeline
- 🇮🇳 Hinglish support via Sarvam AI

## Tech Stack
| Component | Technology |
|---|---|
| Transcription | OpenAI Whisper (small model) |
| LLM | Mistral AI (`open-mistral-7b`) |
| Embeddings | `all-MiniLM-L6-v2` (HuggingFace) |
| Vector Store | ChromaDB |
| Audio Download | yt-dlp + FFmpeg |
| UI | Streamlit |

## Setup (Self-Hosting)

1. Clone the repo
2. Copy `.env.example` → `.env` and fill in your API keys
3. Run `setup.ps1` (Windows) or install from `Requirements.txt`
4. `streamlit run app.py`

## Environment Variables (required in HF Spaces secrets)

| Variable | Description |
|---|---|
| `MISTRAL_API_KEY` | Mistral API key with enabled API access; add as a Space secret |
| `MISTRAL_MODEL` | `mistral-small-2603`; `open-mistral-7b` is retired |
| `LLM_PROVIDER` | `mistral` |
| `SARVAM_API_KEY` | Optional — only needed for Hinglish transcription |
| `WHISPER_MODEL` | `small` (default) or `base` for lower RAM |

## Deploy to Hugging Face Spaces

Create a Space with the **Docker SDK** and **CPU Basic** hardware. Streamlit's
built-in Spaces SDK is deprecated; this repository supplies a Dockerfile that
serves Streamlit on port 8501, installs FFmpeg and Node.js, and uses CPU PyTorch.
`packages.txt` also lists FFmpeg for reference, but Docker installs it explicitly.

Current Hugging Face policy requires a paid plan to create a new Docker Space,
even though CPU Basic has no hourly compute charge. See
[Spaces hardware policy](https://huggingface.co/docs/hub/spaces-overview).

Upload this repository's source files to the Space. A GitHub push alone does not
deploy or automatically synchronize a Hugging Face Space. Never upload `.env`,
local model caches, downloaded audio, or vector databases.

Set `LLM_PROVIDER=mistral` and `MISTRAL_MODEL=mistral-small-2603` as Space variables.
Add `MISTRAL_API_KEY` as a secret, and optionally `SARVAM_API_KEY` for Hinglish.
The Mistral account must permit API inference; hosting does not fix HTTP 429
account restrictions. Secrets stay in Space settings, never in GitHub.

Local Ollama on your Windows machine is not accessible from a hosted Space.
This Docker deployment uses the explicitly configured remote API instead.
CPU transcription is slow; test with a short clip first. CPU Basic storage is
ephemeral, so caches may be downloaded again after restarts.
