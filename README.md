---
title: Govt Scheme Search RAG
emoji: 🏛️
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
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

## Deploy on Hugging Face Spaces (Gradio SDK / ZeroGPU)

1. Create a new Space on [Hugging Face](https://huggingface.co/spaces) with **Gradio** SDK.
2. Under Space **Settings** -> **Variables and secrets**, add:
   - Secret: `GROQ_API_KEY` (Your Groq API key from [console.groq.com](https://console.groq.com/keys)).
   - Variable: `EMBEDDING_LOCAL_FILES_ONLY=false`
3. Connect your GitHub repository (`Anii-hub/Govt_scheme`) or push directly to Hugging Face Spaces.
4. Hugging Face Spaces will automatically launch the Gradio UI from `app.py`.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | Yes | Translation and answer generation |
| `EMBEDDING_LOCAL_FILES_ONLY` | No | Set `false` on Hugging Face Spaces so a cold instance can download the model |
| `EMBEDDING_MODEL` | No | Override the default multilingual embedding model |

