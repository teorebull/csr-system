from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL_NAME = os.environ.get("VECTOR_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.environ.get("VECTOR_CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.environ.get("VECTOR_CHUNK_OVERLAP", "150"))
TOP_K_PER_CLAIM = int(os.environ.get("VECTOR_TOP_K", "3"))

_MODEL: SentenceTransformer | None = None


def load_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _MODEL


def normalize_text(text: str) -> str:
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []

    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = min(length, start + chunk_size)
        if end < length:
            split_at = text.rfind(" ", start + chunk_size // 2, end)
            if split_at > start:
                end = split_at
        chunk = text[start:end].strip()
        if len(chunk) >= 80:
            chunks.append(chunk)
        if end >= length:
            break
        start = max(end - overlap, start + 1)

    return chunks


def build_page_chunks(pages: list[dict]) -> list[dict]:
    chunks = []
    for page in pages:
        text = str(page.get("text", "")).strip()
        if not text:
            continue

        page_chunks = chunk_text(text)
        for chunk_index, chunk_text_value in enumerate(page_chunks, start=1):
            chunks.append(
                {
                    "chunk_id": f"{page.get('document_id', 'doc')}_p{page.get('page_number', 0)}_c{chunk_index}",
                    "document_id": page.get("document_id", ""),
                    "document_name": page.get("document_name", ""),
                    "document_path": page.get("document_path", ""),
                    "page_number": page.get("page_number", 0),
                    "chunk_index": chunk_index,
                    "text": chunk_text_value,
                }
            )
    return chunks


def build_faiss_index(chunks: list[dict]) -> tuple[faiss.IndexFlatIP | None, np.ndarray | None]:
    if not chunks:
        return None, None

    model = load_model()
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    embeddings = embeddings.astype("float32")
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index, embeddings


def save_vector_artifacts(chunks: list[dict], index: faiss.IndexFlatIP | None, artifact_dir: Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    chunks_path = artifact_dir / "chunks.csv"
    index_path = artifact_dir / "index.faiss"
    meta_path = artifact_dir / "meta.json"

    with chunks_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["chunk_id", "document_id", "document_name", "document_path", "page_number", "chunk_index", "text"])
        writer.writeheader()
        for chunk in chunks:
            writer.writerow(chunk)

    if index is not None:
        faiss.write_index(index, str(index_path))

    meta_path.write_text(json.dumps({"embedding_model": EMBEDDING_MODEL_NAME, "chunk_count": len(chunks)}, indent=2), encoding="utf-8")


def retrieve_chunks_for_claims(claims: list[dict], pages: list[dict], artifact_dir: Path, top_k: int = TOP_K_PER_CLAIM) -> list[dict]:
    chunks = build_page_chunks(pages)
    index, _embeddings = build_faiss_index(chunks)
    save_vector_artifacts(chunks, index, artifact_dir)

    if index is None:
        return []

    model = load_model()
    claim_texts = [str(claim.get("claim_text", "")).strip() for claim in claims]
    claim_embeddings = model.encode(claim_texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).astype("float32")
    scores, indices = index.search(claim_embeddings, top_k)

    rows = []
    for claim_index, claim in enumerate(claims):
        claim_id = claim.get("normalized_claim_id", "")
        claim_text = claim.get("claim_text", "")
        for rank, chunk_idx in enumerate(indices[claim_index], start=1):
            if chunk_idx < 0 or chunk_idx >= len(chunks):
                continue
            chunk = chunks[chunk_idx]
            rows.append(
                {
                    "normalized_claim_id": claim_id,
                    "claim_text": claim_text,
                    "query_type": "verification",
                    "query_text": claim_text,
                    "result_rank": rank,
                    "title": f"{chunk['document_name']} p.{chunk['page_number']}",
                    "url": f"local://{chunk['document_id']}/p{chunk['page_number']}/c{chunk['chunk_index']}",
                    "source": chunk.get("document_name", "local_document"),
                    "source_quality_score": 0.8,
                    "source_quality_label": "high",
                    "snippet": chunk["text"][:600],
                    "content_type": "vector_chunk",
                    "extraction_success": True,
                    "extraction_notes": f"faiss_similarity={scores[claim_index][rank - 1]:.4f}",
                    "extracted_text": chunk["text"],
                    "similarity_score": float(scores[claim_index][rank - 1]),
                }
            )

    return rows
