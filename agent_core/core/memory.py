"""
MemoryManager v5.0 — Long-term vector memory with fallback support.

Primary: OpenAI Embeddings (text-embedding-3-small)
Fallback: HuggingFace local embeddings (all-MiniLM-L6-v2, CPU-friendly)
"""

import os
from langchain_chroma import Chroma


class MemoryManager:
    def __init__(self, storage_path="./data/vector_store"):
        self.vector_db = None
        self.embeddings = None
        self._init_embeddings(storage_path)

    def _init_embeddings(self, storage_path: str):
        """Try OpenAI first, fall back to HuggingFace local."""
        # Try OpenAI (primary)
        if self._try_openai(storage_path):
            return

        # Try HuggingFace (fallback — CPU-friendly, ~80MB model)
        if self._try_huggingface(storage_path):
            return

        print("[Memory] ⚠ No embedding provider available. Memory disabled.")

    def _try_openai(self, storage_path: str) -> bool:
        """Attempt to initialize with OpenAI embeddings."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[Memory] ℹ OPENAI_API_KEY not set. Trying fallback...")
            return False

        try:
            from langchain_openai import OpenAIEmbeddings

            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=api_key,
            )
            # Quick validation — embed a single word to test connectivity
            self.embeddings.embed_query("test")

            self.vector_db = Chroma(
                persist_directory=storage_path,
                embedding_function=self.embeddings,
                collection_name="agent_memories",
            )
            print(f"[Memory] ✓ OpenAI embeddings initialized at {storage_path}")
            return True
        except Exception as e:
            print(f"[Memory] ⚠ OpenAI embeddings failed: {e}. Trying fallback...")
            self.embeddings = None
            return False

    def _try_huggingface(self, storage_path: str) -> bool:
        """Attempt to initialize with local HuggingFace embeddings."""
        try:
            from langchain_huggingface import HuggingFaceEmbeddings

            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )

            # Use a different collection to avoid dimension mismatch
            self.vector_db = Chroma(
                persist_directory=storage_path,
                embedding_function=self.embeddings,
                collection_name="agent_memories_local",
            )
            print(f"[Memory] ✓ HuggingFace local embeddings initialized at {storage_path}")
            return True
        except ImportError:
            print("[Memory] ℹ langchain-huggingface not installed. pip install langchain-huggingface sentence-transformers")
            return False
        except Exception as e:
            print(f"[Memory] ✗ HuggingFace embeddings failed: {e}")
            return False

    @property
    def is_available(self) -> bool:
        return self.vector_db is not None

    def recall(self, query: str, k: int = 3) -> str:
        """Retrieves relevant memories for a given query."""
        if not self.vector_db:
            return ""

        try:
            docs = self.vector_db.similarity_search(query, k=k)
            if not docs:
                return ""
            return "\n".join(f"- {doc.page_content}" for doc in docs)
        except Exception as e:
            print(f"[Memory] Recall error: {e}")
            return ""

    def save(self, text: str):
        """Stores a new memory."""
        if not self.vector_db:
            return
        try:
            self.vector_db.add_texts([text])
        except Exception as e:
            print(f"[Memory] Save error: {e}")

    def forget(self, query: str) -> str:
        """Attempts to delete memories matching a query."""
        if not self.vector_db:
            return "Memória não disponível."
        try:
            docs = self.vector_db.similarity_search(query, k=5)
            if not docs:
                return "Nenhuma memória encontrada para esse tópico."
            ids = [doc.metadata.get("id", str(i)) for i, doc in enumerate(docs)]
            self.vector_db._collection.delete(ids=ids)
            return f"Apagadas {len(docs)} memórias relacionadas."
        except Exception as e:
            return f"Erro ao esquecer: {e}"
