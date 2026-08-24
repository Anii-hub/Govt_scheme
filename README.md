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

This repository includes a [`render.yaml`](render.yaml) Blueprint.

1. In Render, choose **New > Blueprint** and select this repository.
2. Render uses the settings in `render.yaml` and prompts for `GROQ_API_KEY`.
   Paste a newly rotated Groq API key. Do not commit it to this repository.
3. Deploy and open the generated `onrender.com` URL.

The free tier may take about a minute to wake after inactivity. Its filesystem
is ephemeral, so the first query after a cold start can take longer while the
embedding model downloads. The Chroma index is committed through Git LFS and is
available with each fresh deployment.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | Yes | Translation and answer generation |
| `EMBEDDING_LOCAL_FILES_ONLY` | No | Set `false` on Render so a cold instance can download the model |
| `EMBEDDING_MODEL` | No | Override the default multilingual embedding model |
