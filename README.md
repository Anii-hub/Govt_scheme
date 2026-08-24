---
title: Govt Scheme Search RAG
emoji: 🏛️
colorFrom: indigo
colorTo: blue
sdk: gradio
app_file: space_app.py
pinned: false
---

# YojnaSearch

An English and Hindi search assistant for Indian government schemes. It uses a
local Chroma index for retrieval and Groq to translate Hindi queries and create
the final answer in the chosen language.

## Run locally

```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Deploy on Render

This repository includes `render.yaml` for a Render Blueprint deployment.

1. In the [Render Dashboard](https://dashboard.render.com/), select **New** -> **Blueprint** and choose this GitHub repository.
2. Render reads `render.yaml`, installs the lightweight runtime dependencies, and starts the FastAPI service.
3. When prompted, set `GROQ_API_KEY` as a secret.

The deployed service serves the web UI at `/`, exposes the API at `/api/search`,
and uses the included SQLite full-text index. It does not load PyTorch, Chroma,
or a sentence-transformer model, keeping RAM use suitable for Render's free tier.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | Yes | Translation and answer generation |

