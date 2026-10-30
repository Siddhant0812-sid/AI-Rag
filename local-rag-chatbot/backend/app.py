import os
import json
import socket
import httpx
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .rag_engine import StudyEngine
from .llm_manager import MultiLLMManager
from .storage import (
    get_documents_metadata,
    get_all_chunks,
    get_document_by_id,
    get_document_file_path,
    update_document_subject
)

app = FastAPI(title="StudyBuddy AI & Shared Document Vault API", version="2.5.0")

# Enable CORS for multi-device network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

study_engine = StudyEngine()
llm_manager = MultiLLMManager()

def get_machine_local_ip() -> str:
    """Detect the host machine's primary local network IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

_cached_public_ip: Optional[str] = None
_cached_public_ip_time: float = 0.0

async def get_machine_public_ip() -> Optional[str]:
    """Detect host machine's public WAN IP address with in-memory caching."""
    global _cached_public_ip, _cached_public_ip_time
    import time
    now = time.time()
    if _cached_public_ip and (now - _cached_public_ip_time < 300):
        return _cached_public_ip
    
    urls = [
        "https://api.ipify.org?format=json",
        "https://api64.ipify.org?format=json",
        "https://httpbin.org/ip"
    ]
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            for u in urls:
                try:
                    resp = await client.get(u)
                    if resp.status_code == 200:
                        data = resp.json()
                        ip = data.get("ip") or data.get("origin", "").split(",")[0].strip()
                        if ip:
                            _cached_public_ip = ip
                            _cached_public_ip_time = now
                            return ip
                except Exception:
                    continue
    except Exception:
        pass
    return _cached_public_ip

# Models
class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "qwen2.5:3b"
    provider: Optional[str] = None # "ollama", "gemini", "openai", "anthropic"
    study_mode: Optional[str] = "general" # "general", "explain", "quiz", "flashcards", "summarize"
    focus_doc_id: Optional[str] = None
    focus_subject: Optional[str] = None
    rag_enabled: Optional[bool] = True
    top_k: Optional[int] = 4
    threshold: Optional[float] = 0.05
    temperature: Optional[float] = 0.7
    system_prompt: Optional[str] = None
    api_key: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 4
    threshold: Optional[float] = 0.05
    focus_doc_id: Optional[str] = None
    focus_subject: Optional[str] = None

class PreloadRequest(BaseModel):
    model: str

class SettingsUpdate(BaseModel):
    ollama_url: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    anthropic_api_key: Optional[str] = None

class KeyTestRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None

class SubjectUpdate(BaseModel):
    subject: str

@app.get("/api/status")
async def get_system_status():
    """Retrieve system health, Ollama status, Cloud LLM keys status, and Study Library statistics."""
    ollama_health = await llm_manager.check_ollama_health()
    docs = get_documents_metadata()
    chunks = get_all_chunks()
    
    total_words = sum(d.get("word_count", 0) for d in docs)
    total_size_bytes = sum(d.get("file_size", 0) for d in docs)
    
    subjects_count = {}
    for d in docs:
        sub = d.get("subject", "General")
        subjects_count[sub] = subjects_count.get(sub, 0) + 1
        
    return {
        "ollama": ollama_health,
        "cloud_providers": {
            "gemini": bool(llm_manager.get_api_key("gemini")),
            "openai": bool(llm_manager.get_api_key("openai")),
            "anthropic": bool(llm_manager.get_api_key("anthropic"))
        },
        "study_library": {
            "document_count": len(docs),
            "chunk_count": len(chunks),
            "total_words": total_words,
            "total_size_bytes": total_size_bytes,
            "subjects": subjects_count,
            "index_ready": study_engine.vectorizer is not None
        }
    }

@app.get("/api/network-info")
async def get_network_info():
    """Returns local network address and public IP for peer, study group & global access."""
    local_ip = get_machine_local_ip()
    public_ip = await get_machine_public_ip()
    port = 8000
    return {
        "local_ip": local_ip,
        "public_ip": public_ip,
        "local_url": f"http://{local_ip}:{port}",
        "public_url": f"http://{public_ip}:{port}" if public_ip else None,
        "url": f"http://{local_ip}:{port}",
        "port": port,
        "hostname": socket.gethostname()
    }

@app.get("/api/models")
async def get_models():
    """Return list of available models across Local Ollama and Cloud (Gemini, OpenAI, Claude)."""
    model_data = await llm_manager.get_all_models()
    return model_data

@app.post("/api/models/preload")
async def preload_model_endpoint(req: PreloadRequest):
    """Pre-warm model into RAM/VRAM so user queries execute with zero cold-start delay."""
    result = await llm_manager.preload_model(req.model)
    return result

@app.post("/api/settings")
async def update_settings(settings: SettingsUpdate):
    """Update Ollama base URL and Cloud API keys."""
    updates = {}
    if settings.ollama_url is not None:
        updates["ollama_url"] = settings.ollama_url.strip()
    if settings.gemini_api_key is not None:
        updates["gemini_api_key"] = settings.gemini_api_key.strip()
    if settings.openai_api_key is not None:
        updates["openai_api_key"] = settings.openai_api_key.strip()
    if settings.openai_base_url is not None:
        updates["openai_base_url"] = settings.openai_base_url.strip()
    if settings.anthropic_api_key is not None:
        updates["anthropic_api_key"] = settings.anthropic_api_key.strip()

    updated_config = llm_manager.update_config(updates)
    health = await llm_manager.check_ollama_health()
    return {
        "status": "updated",
        "health": health,
        "cloud_keys_configured": {
            "gemini": bool(llm_manager.get_api_key("gemini")),
            "openai": bool(llm_manager.get_api_key("openai")),
            "anthropic": bool(llm_manager.get_api_key("anthropic"))
        }
    }

@app.post("/api/settings/test-key")
async def test_key_endpoint(req: KeyTestRequest):
    """Test API key connection, speed latency, and model availability for Gemini, OpenAI, Claude, or Ollama."""
    result = await llm_manager.test_provider_key(
        provider=req.provider,
        api_key=req.api_key,
        base_url=req.base_url
    )
    return result

@app.get("/api/settings")
async def get_settings():
    """Get non-sensitive settings configuration."""
    cfg = llm_manager.config
    # Mask API keys for safe display
    def mask_key(k: Optional[str]) -> str:
        if not k or len(k) < 8:
            return ""
        return f"{k[:4]}...{k[-4:]}"

    return {
        "ollama_url": cfg.get("ollama_url", "http://localhost:11434"),
        "openai_base_url": cfg.get("openai_base_url", "https://api.openai.com/v1"),
        "gemini_configured": bool(llm_manager.get_api_key("gemini")),
        "openai_configured": bool(llm_manager.get_api_key("openai")),
        "anthropic_configured": bool(llm_manager.get_api_key("anthropic")),
        "gemini_masked": mask_key(llm_manager.get_api_key("gemini")),
        "openai_masked": mask_key(llm_manager.get_api_key("openai")),
        "anthropic_masked": mask_key(llm_manager.get_api_key("anthropic"))
    }

@app.get("/api/documents")
async def list_documents():
    """List all shared study documents in the vault."""
    docs = get_documents_metadata()
    return {"documents": docs}

@app.get("/api/documents/{doc_id}/preview")
async def preview_document(doc_id: str):
    """Retrieve full readable text and metadata for in-app reader modal."""
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    full_text = study_engine.get_document_full_text(doc_id)
    if full_text is None:
        raise HTTPException(status_code=404, detail="Document content could not be read")
        
    return {
        "id": doc_id,
        "filename": doc.get("filename"),
        "subject": doc.get("subject", "General"),
        "word_count": doc.get("word_count", 0),
        "file_size": doc.get("file_size", 0),
        "uploaded_at": doc.get("uploaded_at"),
        "text": full_text
    }

@app.get("/api/documents/{doc_id}/download")
async def download_document(doc_id: str):
    """Directly download the original document file so any user on the network can access it."""
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    file_path = get_document_file_path(doc_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file not found on disk")
        
    return FileResponse(
        path=str(file_path),
        filename=doc.get("filename", file_path.name),
        media_type="application/octet-stream"
    )

@app.get("/api/documents/{doc_id}/chunks")
async def get_document_chunks(doc_id: str):
    """Retrieve all study segments belonging to a document."""
    all_chunks = get_all_chunks()
    doc_chunks = [c for c in all_chunks if c.get("doc_id") == doc_id]
    if not doc_chunks:
        raise HTTPException(status_code=404, detail="Document chunks not found")
    return {"chunks": doc_chunks}

@app.post("/api/documents/{doc_id}/subject")
async def set_document_subject(doc_id: str, payload: SubjectUpdate):
    """Update the academic subject tag of a document."""
    success = update_document_subject(doc_id, payload.subject)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "success", "doc_id": doc_id, "subject": payload.subject}

@app.post("/api/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    subject: Optional[str] = Form(None)
):
    """Upload and store study documents in the shared vault."""
    results = []
    errors = []
    for file in files:
        try:
            content = await file.read()
            doc_meta = study_engine.ingest_document(file.filename, content, subject=subject)
            results.append(doc_meta)
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})

    return {
        "success": len(results) > 0,
        "uploaded": results,
        "errors": errors,
        "total_documents": len(get_documents_metadata())
    }

@app.post("/api/documents/load-samples")
async def load_sample_documents():
    """Load built-in demonstration study guides into the shared library."""
    loaded = study_engine.load_samples()
    return {
        "status": "success",
        "loaded": loaded,
        "total_documents": len(get_documents_metadata())
    }

@app.delete("/api/documents/{doc_id}")
async def delete_document_endpoint(doc_id: str):
    """Delete a document and purge its chunks from the shared library."""
    success = study_engine.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "doc_id": doc_id}

@app.post("/api/documents/clear")
async def clear_documents_endpoint():
    """Clear all documents and chunks from the shared library."""
    study_engine.clear_all()
    return {"status": "cleared"}

@app.post("/api/search")
async def search_endpoint(req: SearchRequest):
    """Test retrieval directly without calling LLM."""
    results = study_engine.search(
        req.query,
        top_k=req.top_k or 4,
        threshold=req.threshold or 0.05,
        filter_doc_id=req.focus_doc_id,
        filter_subject=req.focus_subject
    )
    return {"query": req.query, "results": results, "count": len(results)}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    StudyBuddy AI Chat endpoint supporting Ollama Local, Google Gemini, OpenAI, and Claude.
    Streams with Server-Sent Events (SSE).
    """
    retrieved_chunks = []
    if req.rag_enabled:
        retrieved_chunks = study_engine.search(
            req.message,
            top_k=req.top_k or 4,
            threshold=req.threshold or 0.05,
            filter_doc_id=req.focus_doc_id,
            filter_subject=req.focus_subject
        )

    # Build pedagogical study prompt
    sys_prompt, user_prompt = study_engine.build_study_prompt(
        query=req.message,
        retrieved_chunks=retrieved_chunks,
        study_mode=req.study_mode or "general",
        custom_system_prompt=req.system_prompt
    )

    model_name = req.model or "qwen2.5:3b"

    async def event_generator():
        # 1. Send the referenced study notes event
        sources_payload = {
            "type": "sources",
            "study_mode": req.study_mode or "general",
            "sources": [
                {
                    "doc_id": c["doc_id"],
                    "filename": c["filename"],
                    "subject": c.get("subject", "General"),
                    "chunk_index": c["chunk_index"],
                    "score": c["score"],
                    "text": c["text"]
                }
                for c in retrieved_chunks
            ]
        }
        yield f"data: {json.dumps(sources_payload)}\n\n"

        # 2. Stream generated tokens across selected provider (Ollama / Gemini / OpenAI / Claude)
        async for token in llm_manager.stream_generate(
            model=model_name,
            prompt=user_prompt,
            system_prompt=sys_prompt,
            temperature=req.temperature or 0.7,
            provider=req.provider,
            api_key=req.api_key
        ):
            token_payload = {"type": "token", "token": token}
            yield f"data: {json.dumps(token_payload)}\n\n"

        # 3. Signal completion
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# Mount frontend static files
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
