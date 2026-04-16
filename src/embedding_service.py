"""Real Embedding and Vector Store Service using sentence-transformers + FAISS"""

import os
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

# Lazy imports to avoid startup errors
_sentence_transformers = None
_faiss = None


def _get_sentence_transformers():
    global _sentence_transformers
    if _sentence_transformers is None:
        from sentence_transformers import SentenceTransformer
        _sentence_transformers = SentenceTransformer
    return _sentence_transformers


def _get_faiss():
    global _faiss
    if _faiss is None:
        import faiss
        _faiss = faiss
    return _faiss


# Use multilingual model — much better for Vietnamese text
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CACHE_DIR = Path(__file__).parent.parent / "cache"
INDEX_CACHE = CACHE_DIR / "faiss_index.pkl"


class EmbeddingService:
    def __init__(self):
        self.model = None
        self.index = None
        self.documents: List[Dict[str, Any]] = []
        self.embedding_dim = 384
        self._query_cache: Dict[str, np.ndarray] = {}
        self._load_model()

    def _load_model(self):
        """Load sentence transformer model"""
        try:
            SentenceTransformer = _get_sentence_transformers()
            print(f"   Loading embedding model: {EMBEDDING_MODEL}")
            self.model = SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            print(f"   [OK] Embedding model loaded (dim={self.embedding_dim})")
        except Exception as e:
            print(f"   [WARN] Could not load embedding model: {e}")
            self.model = None

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string"""
        if self.model is None:
            return np.zeros(self.embedding_dim, dtype=np.float32)
        cached = self._query_cache.get(text)
        if cached is not None:
            return cached
        vec = self.model.encode([text], normalize_embeddings=True)[0]
        vec = vec.astype(np.float32)
        if len(self._query_cache) > 256:
            self._query_cache.clear()
        self._query_cache[text] = vec
        return vec

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embed a batch of texts (faster)"""
        if self.model is None:
            return np.zeros((len(texts), self.embedding_dim), dtype=np.float32)
        vecs = self.model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
        return vecs.astype(np.float32)

    def create_index(self, documents: List[Dict[str, Any]]) -> None:
        """Build FAISS index from documents, with disk cache"""
        self.documents = documents

        # Try loading from cache first
        if INDEX_CACHE.exists():
            try:
                self._load_index_from_cache()
                # Verify cache matches current documents
                if len(self.documents) == self._cached_doc_count:
                    print(f"   [OK] Loaded FAISS index from cache ({len(documents)} chunks)")
                    return
                else:
                    print("   Cache mismatch, rebuilding index...")
            except Exception:
                print("   Cache invalid, rebuilding index...")

        # Build fresh index
        self._build_index(documents)
        self._save_index_to_cache()

    def _build_index(self, documents: List[Dict[str, Any]]) -> None:
        """Build FAISS index from scratch"""
        if self.model is None or not documents:
            return

        faiss = _get_faiss()
        texts = [doc["text"] for doc in documents]
        print(f"   Building FAISS index for {len(texts)} chunks...")
        embeddings = self.embed_batch(texts)

        # Inner product on normalized vectors == cosine similarity
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.index.add(embeddings)
        self._cached_doc_count = len(documents)
        print(f"   [OK] FAISS index built ({len(texts)} vectors)")

    def _save_index_to_cache(self) -> None:
        """Persist index + documents to disk"""
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            faiss = _get_faiss()
            # Serialize FAISS index bytes
            index_bytes = faiss.serialize_index(self.index)
            cache_data = {
                "index_bytes": index_bytes,
                "documents": self.documents,
                "doc_count": len(self.documents),
                "embedding_dim": self.embedding_dim,
            }
            with open(INDEX_CACHE, "wb") as f:
                pickle.dump(cache_data, f)
            print(f"   [OK] Index cached to {INDEX_CACHE}")
        except Exception as e:
            print(f"   [WARN] Could not cache index: {e}")

    def _load_index_from_cache(self) -> None:
        """Load index + documents from disk"""
        faiss = _get_faiss()
        with open(INDEX_CACHE, "rb") as f:
            cache_data = pickle.load(f)
        self.index = faiss.deserialize_index(cache_data["index_bytes"])
        self.documents = cache_data["documents"]
        self._cached_doc_count = cache_data["doc_count"]
        self.embedding_dim = cache_data.get("embedding_dim", self.embedding_dim)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Semantic search — returns top_k most relevant documents"""
        if self.model is None or self.index is None or not self.documents:
            return []

        query_vec = self.embed_text(query).reshape(1, -1)
        actual_k = min(top_k, len(self.documents))
        scores, indices = self.index.search(query_vec, actual_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and float(score) > 0.1:  # Minimum similarity threshold
                doc = dict(self.documents[idx])
                doc["score"] = float(score)
                results.append(doc)

        return results

    def invalidate_cache(self) -> None:
        """Delete cache to force rebuild on next start"""
        if INDEX_CACHE.exists():
            INDEX_CACHE.unlink()
            print("   Cache invalidated.")
