import uuid
import logging
from contextlib import asynccontextmanager
from typing import Optional, Literal
from pathlib import Path
from fastapi import FastAPI, Request, Query, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from findex.index import InvertedIndex
from findex.scoring import BM25Scorer, TfIdfScorer
from findex.search import execute_search
from findex.web.config import settings

logger = logging.getLogger("findex.web")

ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Завантаження індексу один раз при старті
    idx_path = Path(settings.index_path)
    if idx_path.exists():
        ml_models["index"] = InvertedIndex.load_pickle(str(idx_path))
    else:
        ml_models["index"] = None
    yield
    ml_models.clear()

app = FastAPI(title="Findex Web API", lifespan=lifespan)
templates = Jinja2Templates(directory="src/findex/web/templates")

def get_index() -> InvertedIndex:
    idx = ml_models.get("index")
    if idx is None:
        raise HTTPException(status_code=503, detail="Index not loaded")
    return idx

@app.get("/health")
def health(idx: InvertedIndex = Depends(get_index)):
    return {"status": "ok"}

@app.get("/stats")
def stats(idx: InvertedIndex = Depends(get_index)):
    return {
        "total_terms": len(idx.index),
        "total_documents": len(idx.metadata)
    }

# Використовуємо async def для неблокуючого обробітку I/O / пошуку
@app.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    k: int = Query(5, ge=1, le=50),
    scorer_name: Literal["bm25", "tfidf"] = "bm25",
    page: int = Query(1, ge=1),
    idx: InvertedIndex = Depends(get_index)
):
    try:
        scorer = BM25Scorer() if scorer_name == "bm25" else TfIdfScorer()
        results = execute_search(idx, q, scorer, top_k=k * page)
        # Проста пагінація
        start = (page - 1) * k
        paginated = results[start:start + k]
        return {
            "query": q,
            "page": page,
            "results": [{"doc_id": r.doc_id, "score": r.score, "filename": r.filename} for r in paginated]
        }
    except Exception as e:
        req_id = uuid.uuid4()
        logger.error(f"Req ID {req_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error (ID: {req_id})")

@app.get("/docs/{doc_id}")
def get_doc(doc_id: int, idx: InvertedIndex = Depends(get_index)):
    meta = idx.metadata.get(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found")
    # Читаємо вміст файлу документа
    doc_path = Path(meta.filename)
    text = doc_path.read_text(encoding="utf-8", errors="ignore") if doc_path.exists() else "File not found on disk."
    return {"doc_id": meta.doc_id, "filename": meta.filename, "text": text}

@app.get("/", response_class=HTMLResponse)
def index_page(request: Request):
	return templates.TemplateResponse(request, "index.html", {})