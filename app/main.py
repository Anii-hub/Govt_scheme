from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.rag.query_parser import parse_query
from app.rag.search import search_schemes
from app.rag.answer_generator import generate_answer


# =========================================================
# FastAPI Application
# =========================================================

app = FastAPI(
    title="Indian Government Schemes API",
    description="RAG API for discovering Indian government schemes",
    version="1.0.0",
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


# =========================================================
# Static Frontend
# =========================================================

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# =========================================================
# Root — serve the frontend
# =========================================================

@app.get("/", include_in_schema=False)
def root():
    index_html = FRONTEND_DIR / "index.html"
    if index_html.exists():
        return FileResponse(str(index_html))
    return {
        "status": "ok",
        "message": "Indian Government Schemes API is running",
        "version": "1.0.0",
    }


# =========================================================
# Health Check
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
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
        # Parse query
        # -------------------------------------------------

        parsed_query = parse_query(query)

        # -------------------------------------------------
        # Retrieve schemes
        # -------------------------------------------------

        results = search_schemes(
            query=query,
            semantic_k=100,
            final_k=5,
        )

        # -------------------------------------------------
        # Generate structured answer
        # -------------------------------------------------

        answer = generate_answer(
            query,
            results,
        )

        # -------------------------------------------------
        # Return API response
        # -------------------------------------------------

        return {
            "success": True,
            "query": query,

            "parsed_query": {
                "state": parsed_query.get("state"),
                "category": parsed_query.get("category"),
            },

            "results": answer,
        }

    except ValueError as error:

        print("\nVALUE ERROR:")
        print(error)

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    except Exception as error:

        print("\nUNEXPECTED API ERROR:")
        print(error)

        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the query.",
        )