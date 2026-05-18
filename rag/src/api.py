"""FastAPI 接口封装"""

import json
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.rag_chain import RAGChain


app = FastAPI(title="本地知识库 RAG 问答系统", version="1.0")

with open("config/config.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

rag = RAGChain()
index_ready = False


class QueryRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    top_k: int = Field(default=5, ge=1, le=20, description="检索片段数")


class Source(BaseModel):
    source: str
    score: float
    preview: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.on_event("startup")
async def startup():
    global index_ready
    db_path = Path("chroma_db")
    if db_path.exists() and any(db_path.iterdir()):
        rag.load_index()
        index_ready = True
    else:
        try:
            chunks = rag.load_documents()
            rag.build_index(chunks)
            index_ready = True
        except Exception:
            index_ready = False


@app.post("/rag/query", response_model=QueryResponse)
async def rag_query(req: QueryRequest):
    if not index_ready:
        raise HTTPException(status_code=503, detail="知识库索引未就绪")

    result = rag.answer(req.question, req.top_k)
    return QueryResponse(
        answer=result["answer"],
        sources=[Source(**s) for s in result["sources"]],
    )


@app.post("/rag/stream")
async def rag_stream(req: QueryRequest):
    if not index_ready:
        raise HTTPException(status_code=503, detail="知识库索引未就绪")

    async def generate():
        for chunk in rag.stream_answer(req.question, req.top_k):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/health")
async def health():
    return {"status": "ok", "index_ready": index_ready}
