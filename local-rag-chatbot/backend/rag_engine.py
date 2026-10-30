import io
import re
import math
import uuid
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pypdf

from .storage import (
    get_documents_metadata,
    save_documents_metadata,
    get_all_chunks,
    save_all_chunks,
    save_uploaded_file,
    get_document_by_id,
    get_document_file_path,
    infer_subject_from_filename,
    delete_document as storage_delete_doc,
    clear_all_storage as storage_clear_all
)
from .sample_docs import SAMPLE_STUDY_DOCUMENTS

class BM25Retriever:
    """Lightweight in-memory BM25 retrieval implementation."""
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.corpus_size: int = 0

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b\w{2,}\b", text.lower())

    def fit(self, texts: List[str]):
        self.corpus = [self._tokenize(t) for t in texts]
        self.corpus_size = len(self.corpus)
        if self.corpus_size == 0:
            self.avg_doc_len = 0.0
            return

        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avg_doc_len = sum(self.doc_lengths) / max(1, self.corpus_size)

        self.doc_freqs = {}
        for doc in self.corpus:
            seen_tokens = set(doc)
            for token in seen_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.idf = {}
        for token, freq in self.doc_freqs.items():
            # Standard Lucene/BM25 IDF formula
            self.idf[token] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query: str) -> np.ndarray:
        if self.corpus_size == 0:
            return np.array([])
            
        q_tokens = self._tokenize(query)
        scores = np.zeros(self.corpus_size)

        for i, doc in enumerate(self.corpus):
            doc_len = self.doc_lengths[i]
            if doc_len == 0:
                continue

            term_counts: Dict[str, int] = {}
            for t in doc:
                term_counts[t] = term_counts.get(t, 0) + 1

            doc_score = 0.0
            for qt in q_tokens:
                if qt in term_counts:
                    tf = term_counts[qt]
                    idf_val = self.idf.get(qt, 0.0)
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1e-6, self.avg_doc_len)))
                    doc_score += idf_val * (numerator / max(1e-6, denominator))

            scores[i] = doc_score

        # Normalize scores to 0.0 - 1.0
        max_score = np.max(scores) if len(scores) > 0 else 0
        if max_score > 0:
            return scores / max_score
        return scores


class StudyEngine:
    """Core StudyBuddy engine managing document parsing, chunking, indexing, and study mode synthesis."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.bm25: Optional[BM25Retriever] = None
        self.cached_chunks: List[Dict[str, Any]] = []
        self._build_index()

    def _build_index(self):
        """Build or refresh vector and BM25 index from stored chunks."""
        self.cached_chunks = get_all_chunks()
        if not self.cached_chunks:
            self.vectorizer = None
            self.tfidf_matrix = None
            self.bm25 = None
            return

        texts = [chunk["text"] for chunk in self.cached_chunks]
        try:
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                stop_words='english',
                sublinear_tf=True,
                max_features=25000
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            self.bm25 = BM25Retriever()
            self.bm25.fit(texts)
        except Exception as e:
            print(f"Error building vector index: {e}")
            self.vectorizer = None
            self.tfidf_matrix = None
            self.bm25 = None

    def extract_text(self, filename: str, content_bytes: bytes) -> str:
        """Extract plain text from heterogeneous study document formats."""
        ext = Path(filename).suffix.lower()
        
        if ext == ".pdf":
            try:
                reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                pages_text = []
                for idx, page in enumerate(reader.pages):
                    page_content = page.extract_text() or ""
                    if page_content.strip():
                        pages_text.append(f"[Page {idx + 1}]\n{page_content}")
                return "\n\n".join(pages_text)
            except Exception as e:
                return f"[PDF parsing error: {e}]"
            
        elif ext in [".md", ".markdown", ".txt"]:
            return content_bytes.decode("utf-8", errors="replace")
            
        elif ext == ".csv":
            text_stream = io.StringIO(content_bytes.decode("utf-8", errors="replace"))
            csv_reader = csv.reader(text_stream)
            rows = []
            header = None
            for row_idx, row in enumerate(csv_reader):
                if row_idx == 0:
                    header = row
                    rows.append(f"Columns: {', '.join(row)}")
                else:
                    if header and len(header) == len(row):
                        pairs = [f"{header[i]}: {row[i]}" for i in range(len(row))]
                        rows.append(f"Row {row_idx}: {'; '.join(pairs)}")
                    else:
                        rows.append(f"Row {row_idx}: {', '.join(row)}")
            return "\n".join(rows)
            
        elif ext == ".json":
            try:
                data = json.loads(content_bytes.decode("utf-8", errors="replace"))
                return json.dumps(data, indent=2)
            except Exception:
                return content_bytes.decode("utf-8", errors="replace")
                
        else:
            # Fallback text extraction
            return content_bytes.decode("utf-8", errors="replace")

    def recursive_chunk_text(self, text: str, doc_id: str, filename: str, subject: str = "General") -> List[Dict[str, Any]]:
        """Split text into semantic chunks with overlap."""
        if not text or not text.strip():
            return []

        paragraphs = text.split("\n\n")
        raw_chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(para) <= self.chunk_size:
                if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                    current_chunk = f"{current_chunk}\n\n{para}".strip()
                else:
                    if current_chunk:
                        raw_chunks.append(current_chunk)
                    current_chunk = para
            else:
                # Break large paragraph by sentences
                sub_segments = re.split(r"(?<=[.!?])\s+", para)
                for seg in sub_segments:
                    seg = seg.strip()
                    if not seg:
                        continue
                    if len(current_chunk) + len(seg) + 1 <= self.chunk_size:
                        current_chunk = f"{current_chunk} {seg}".strip()
                    else:
                        if current_chunk:
                            raw_chunks.append(current_chunk)
                        current_chunk = seg

        if current_chunk:
            raw_chunks.append(current_chunk)

        # Apply sliding overlap
        final_chunks: List[Dict[str, Any]] = []
        for i, chunk_str in enumerate(raw_chunks):
            chunk_text = chunk_str
            if i > 0 and self.chunk_overlap > 0:
                prev_text = raw_chunks[i - 1]
                overlap_text = prev_text[-self.chunk_overlap:]
                if " " in overlap_text:
                    overlap_text = overlap_text[overlap_text.find(" ") + 1:]
                chunk_text = f"...{overlap_text}\n{chunk_text}"

            chunk_id = f"{doc_id}_chunk_{i + 1}"
            final_chunks.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "filename": filename,
                "subject": subject,
                "chunk_index": i + 1,
                "total_chunks": len(raw_chunks),
                "text": chunk_text.strip(),
                "char_count": len(chunk_text.strip()),
                "word_count": len(chunk_text.split())
            })

        return final_chunks

    def ingest_document(self, filename: str, content_bytes: bytes, subject: Optional[str] = None) -> Dict[str, Any]:
        """Ingest, parse, chunk, and index a study document into the shared vault."""
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        saved_path = save_uploaded_file(f"{doc_id}_{filename}", content_bytes)
        
        assigned_subject = subject.strip() if subject and subject.strip() else infer_subject_from_filename(filename)
        extracted_text = self.extract_text(filename, content_bytes)
        chunks = self.recursive_chunk_text(extracted_text, doc_id, filename, assigned_subject)
        
        all_chunks = get_all_chunks()
        all_chunks.extend(chunks)
        save_all_chunks(all_chunks)

        metadata_list = get_documents_metadata()
        doc_meta = {
            "id": doc_id,
            "filename": filename,
            "saved_file": saved_path.name,
            "subject": assigned_subject,
            "file_size": len(content_bytes),
            "chunk_count": len(chunks),
            "word_count": len(extracted_text.split()),
            "char_count": len(extracted_text),
            "uploaded_at": str(np.datetime64('now'))
        }
        metadata_list.append(doc_meta)
        save_documents_metadata(metadata_list)

        # Refresh in-memory vector index
        self._build_index()
        return doc_meta

    def get_document_full_text(self, doc_id: str) -> Optional[str]:
        """Retrieve full text of a stored document for in-app reader preview."""
        doc = get_document_by_id(doc_id)
        if not doc:
            return None
        
        file_path = get_document_file_path(doc_id)
        if file_path and file_path.exists():
            try:
                content_bytes = file_path.read_bytes()
                return self.extract_text(doc.get("filename", file_path.name), content_bytes)
            except Exception:
                pass

        # Fallback to reconstructing from chunks
        chunks = [c for c in get_all_chunks() if c.get("doc_id") == doc_id]
        if chunks:
            chunks.sort(key=lambda x: x.get("chunk_index", 0))
            return "\n\n".join(c.get("text", "") for c in chunks)
            
        return None

    def load_samples(self) -> List[Dict[str, Any]]:
        """Load built-in demonstration study guides into the shared library."""
        loaded = []
        for doc_def in SAMPLE_STUDY_DOCUMENTS:
            meta = self.ingest_document(
                doc_def["filename"],
                doc_def["content"].encode("utf-8"),
                subject=doc_def.get("subject", "General")
            )
            loaded.append(meta)
        return loaded

    def delete_document(self, doc_id: str) -> bool:
        """Purge document and its chunks from shared library."""
        success = storage_delete_doc(doc_id)
        if success:
            self._build_index()
        return success

    def clear_all(self):
        """Purge all documents from study library."""
        storage_clear_all()
        self._build_index()

    def search(
        self,
        query: str,
        top_k: int = 4,
        threshold: float = 0.05,
        filter_doc_id: Optional[str] = None,
        filter_subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search relevant study chunks using TF-IDF cosine + BM25 ranking.
        Supports filtering by specific document or subject category.
        """
        if not self.cached_chunks or not self.vectorizer or self.tfidf_matrix is None:
            return []

        # 1. Dense TF-IDF Cosine Similarity
        try:
            q_vec = self.vectorizer.transform([query])
            tfidf_scores = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        except Exception:
            tfidf_scores = np.zeros(len(self.cached_chunks))

        # 2. Sparse BM25 Lexical Ranking
        bm25_scores = np.zeros(len(self.cached_chunks))
        if self.bm25:
            bm25_scores = self.bm25.get_scores(query)

        # 3. Hybrid Combination with exact phrase bonus
        q_lower = query.lower()
        combined_results = []

        for idx, chunk in enumerate(self.cached_chunks):
            # Apply filters if requested
            if filter_doc_id and chunk.get("doc_id") != filter_doc_id:
                continue
            if filter_subject and chunk.get("subject", "General").lower() != filter_subject.lower():
                continue

            t_score = float(tfidf_scores[idx]) if idx < len(tfidf_scores) else 0.0
            b_score = float(bm25_scores[idx]) if idx < len(bm25_scores) else 0.0
            
            hybrid = 0.5 * t_score + 0.5 * b_score
            
            # Boost exact phrase matches
            if q_lower in chunk["text"].lower():
                hybrid = min(1.0, hybrid + 0.15)

            if hybrid >= threshold:
                combined_results.append({
                    "chunk_id": chunk["chunk_id"],
                    "doc_id": chunk["doc_id"],
                    "filename": chunk["filename"],
                    "subject": chunk.get("subject", "General"),
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    "score": round(float(hybrid), 4),
                    "tfidf_score": round(float(t_score), 4),
                    "bm25_score": round(float(b_score), 4)
                })

        combined_results.sort(key=lambda x: x["score"], reverse=True)
        return combined_results[:top_k]

    def build_study_prompt(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        study_mode: str = "general",
        custom_system_prompt: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Builds pedagogical system and user prompts tuned for the chosen study mode:
        - general: Encouraging, structured study partner
        - explain: Analogies, step-by-step intuition, simplified breakdowns
        - quiz: 3-4 practice test questions with answer choices and explanations
        - flashcards: High-yield Q&A cards
        - summarize: High-yield revision bullet points, formulas, common pitfalls
        """
        base_personality = (
            "You are StudyBuddy AI, an intelligent, enthusiastic, and supportive peer study partner. "
            "Your mission is to help students learn deeply, ace their exams, understand tough concepts, and test their memory. "
            "Always be encouraging, clear, and pedagogically sound. Use clear Markdown, code blocks, bullet points, and math notation ($...$) where fitting. "
        )

        mode_instructions = {
            "general": (
                "Provide a comprehensive, engaging answer. Break down complex ideas logically. "
                "Whenever your answer references facts from the shared study notes, mention the source notes naturally (e.g. '[Referenced from: filename]'). "
                "End with a short, helpful check-in question or suggestion for what to study next."
            ),
            "explain": (
                "Act as an intuitive tutor. Explain the concept like you're talking to a curious student: "
                "1. Provide a quick 1-sentence high-level summary. "
                "2. Use a vivid real-world analogy or visual metaphor. "
                "3. Walk through the core mechanism step-by-step. "
                "4. Highlight the #1 key takeaway to remember for tests."
            ),
            "quiz": (
                "Act as a practice exam generator. Create a mini practice quiz (3-4 questions) based on the topic. "
                "Format each question clearly with options A, B, C, D (or a short-answer prompt). "
                "Below the questions, provide an 'Answer Key & Detailed Explanations' section explaining WHY the correct option is right and why common distractors are wrong."
            ),
            "flashcards": (
                "Generate 4 to 5 high-yield study flashcards based on the material. "
                "Format each card as:\n"
                "### 📇 Card [Number]: [Topic/Concept Name]\n"
                "- **Front (Question / Prompt)**: [Targeted test question or definition prompt]\n"
                "- **Back (Answer / Key Fact)**: [Concise, punchy answer with essential formulas/definitions]\n"
                "- **Exam Tip**: [Quick mnemonic or tip]"
            ),
            "summarize": (
                "Synthesize a high-yield 'Cram Sheet / Revision Summary' of this material: "
                "1. **Core Definitions**: 3-5 vital terms. "
                "2. **Key Concepts & Principles**: Bulleted essential takeaways. "
                "3. **Formulas / Algorithms / Rules**: Quick reference list. "
                "4. **Common Exam Traps / Gotchas**: Mistakes students frequently make."
            )
        }

        mode_instruction = mode_instructions.get(study_mode, mode_instructions["general"])
        
        system_prompt = custom_system_prompt.strip() if custom_system_prompt and custom_system_prompt.strip() else f"{base_personality}\n\nSTUDY MODE INSTRUCTION:\n{mode_instruction}"

        # If no study notes are retrieved, answer using general academic knowledge
        if not retrieved_chunks:
            user_prompt = (
                f"Student's Study Question: {query}\n\n"
                f"[Context note: No matching notes found in the shared study vault for this query. "
                f"Please draw on your general academic knowledge to provide an outstanding, encouraging study answer, and let the student know they can also upload their class notes to the Shared Study Library for even more specific help.]"
            )
            return system_prompt, user_prompt

        # Build study notes context blocks
        context_blocks = []
        for i, c in enumerate(retrieved_chunks):
            block = (
                f"--- [Shared Study Note {i + 1}: {c['filename']} (Subject: {c.get('subject', 'General')}, Relevance: {int(c['score'] * 100)}%)] ---\n"
                f"{c['text']}"
            )
            context_blocks.append(block)

        formatted_context = "\n\n".join(context_blocks)
        user_prompt = (
            f"=== SHARED STUDY LIBRARY NOTES ===\n"
            f"{formatted_context}\n"
            f"=== END OF NOTES ===\n\n"
            f"Student's Study Request: {query}\n\n"
            f"Respond using the study notes above to guide your answer according to the active study mode ({study_mode})."
        )

        return system_prompt, user_prompt
