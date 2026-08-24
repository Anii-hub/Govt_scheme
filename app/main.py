# app/main.py

import logging
from typing import Literal

from app.config import CHROMA_PATH

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.rag.search import search_schemes
from app.rag.answer_generator import generate_answer, translate_query_for_search


logging.basicConfig(level=logging.INFO)


# =========================================================
# FastAPI Application
# =========================================================

app = FastAPI(
    title="Indian Government Schemes API",
    description="RAG API for discovering Indian government schemes",
    version="2.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Request Model
# =========================================================

class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language government scheme query",
    )
    language: Literal["english", "hindi"] = "english"


import os
from fastapi.staticfiles import StaticFiles

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

@app.get("/")
def root():
    from fastapi.responses import FileResponse
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "status": "ok",
        "message": "Indian Government Schemes API is running",
        "version": "2.0.0",
    }


# =========================================================
# Health Check
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "vector_store_present": os.path.exists(CHROMA_PATH),
    }


# =========================================================
# Search Endpoint
# =========================================================

@app.post("/api/search")
def search(request: SearchRequest):

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    try:

        # -------------------------------------------------
        # Retrieve schemes
        # -------------------------------------------------

        search_query = translate_query_for_search(
            query,
            request.language,
        )

        search_output = search_schemes(
            query=search_query,
            final_k=5,
        )

        results          = search_output["results"]
        no_match_reason  = search_output["no_match_reason"]
        parsed           = search_output["parsed"]

        # -------------------------------------------------
        # Generate structured answer
        # -------------------------------------------------

        answer = generate_answer(
            query,
            results,
            language=request.language,
        )

        # -------------------------------------------------
        # Return API response
        # -------------------------------------------------

        return {
            "success": True,
            "query": query,
            "language": request.language,

            "parsed_query": {
                "state":    parsed.get("state"),
                "category": parsed.get("category"),
                "age":      parsed.get("age"),
                "gender":   parsed.get("gender"),
                "income":   parsed.get("income"),
            },

            "no_match_reason": no_match_reason,

            "results": answer,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=503,
            detail=str(error),
        )

    except Exception as error:

        logging.exception("Unexpected error during search")

        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the query.",
        )
