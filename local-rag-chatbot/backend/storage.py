import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DOCS_DIR = DATA_DIR / "documents"
METADATA_FILE = DATA_DIR / "metadata.json"
CHUNKS_FILE = DATA_DIR / "chunks.json"

def init_storage():
    """Ensure data directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    if not METADATA_FILE.exists():
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    if not CHUNKS_FILE.exists():
        with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

def get_documents_metadata() -> List[Dict[str, Any]]:
    """Retrieve metadata for all ingested study documents."""
    init_storage()
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            docs = json.load(f)
            # Ensure each doc has a subject field
            for d in docs:
                if "subject" not in d:
                    d["subject"] = infer_subject_from_filename(d.get("filename", ""))
            return docs
    except Exception:
        return []

def get_document_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve metadata for a specific document."""
    docs = get_documents_metadata()
    for d in docs:
        if d.get("id") == doc_id:
            return d
    return None

def get_document_file_path(doc_id: str) -> Optional[Path]:
    """Retrieve physical path to the stored document."""
    doc = get_document_by_id(doc_id)
    if not doc:
        return None
    
    # Check saved_file first, then filename
    candidates = [
        doc.get("saved_file"),
        f"{doc_id}_{doc.get('filename')}",
        doc.get("filename")
    ]
    for c in candidates:
        if c:
            p = DOCS_DIR / c
            if p.exists():
                return p
    return None

def save_documents_metadata(metadata: List[Dict[str, Any]]):
    """Save metadata for all ingested study documents."""
    init_storage()
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def update_document_subject(doc_id: str, subject: str) -> bool:
    """Update subject category for a document."""
    metadata = get_documents_metadata()
    found = False
    for doc in metadata:
        if doc.get("id") == doc_id:
            doc["subject"] = subject
            found = True
            break
    if found:
        save_documents_metadata(metadata)
    return found

def get_all_chunks() -> List[Dict[str, Any]]:
    """Retrieve all document chunks."""
    init_storage()
    try:
        with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_all_chunks(chunks: List[Dict[str, Any]]):
    """Save all document chunks to disk."""
    init_storage()
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

def save_uploaded_file(filename: str, content: bytes) -> Path:
    """Save raw file to storage."""
    init_storage()
    dest = DOCS_DIR / filename
    with open(dest, "wb") as f:
        f.write(content)
    return dest

def infer_subject_from_filename(filename: str) -> str:
    """Auto-detect study subject based on common naming patterns."""
    fn = filename.lower()
    if any(k in fn for k in ["cs", "code", "algorithm", "data_structure", "python", "software", "network", "web"]):
        return "Computer Science"
    elif any(k in fn for k in ["bio", "cell", "genetic", "dna", "anatomy", "medical", "organ"]):
        return "Biology"
    elif any(k in fn for k in ["phys", "mechanic", "thermo", "quantum", "electr", "gravity"]):
        return "Physics"
    elif any(k in fn for k in ["math", "calculus", "algebra", "stats", "matrix", "geometry"]):
        return "Mathematics"
    elif any(k in fn for k in ["chem", "molecule", "reaction", "organic", "acid"]):
        return "Chemistry"
    elif any(k in fn for k in ["hist", "war", "century", "civic", "politic"]):
        return "History"
    elif any(k in fn for k in ["econ", "finance", "market", "business", "trade"]):
        return "Economics"
    return "General"

def delete_document(doc_id: str) -> bool:
    """Delete a document and its associated chunks."""
    init_storage()
    metadata = get_documents_metadata()
    target_doc = None
    remaining_docs = []
    for doc in metadata:
        if doc.get("id") == doc_id:
            target_doc = doc
        else:
            remaining_docs.append(doc)
            
    if not target_doc:
        return False

    # Remove physical file if exists
    for candidate in [target_doc.get("saved_file"), f"{doc_id}_{target_doc.get('filename')}", target_doc.get("filename")]:
        if candidate:
            file_path = DOCS_DIR / candidate
            if file_path.exists():
                try:
                    os.remove(file_path)
                    break
                except Exception:
                    pass

    save_documents_metadata(remaining_docs)

    # Filter out chunks
    chunks = get_all_chunks()
    remaining_chunks = [c for c in chunks if c.get("doc_id") != doc_id]
    save_all_chunks(remaining_chunks)
    return True

def clear_all_storage():
    """Remove all documents and chunks from storage."""
    init_storage()
    save_documents_metadata([])
    save_all_chunks([])
    for item in DOCS_DIR.glob("*"):
        if item.is_file():
            try:
                item.unlink()
            except Exception:
                pass
