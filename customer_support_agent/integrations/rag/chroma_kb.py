from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from langchain_text_splitters import RecursiveCharacterTextSplitter

from customer_support_agent.core.settings import Settings, get_settings


class KnowledgeBaseService:
    def __init__(self,settings:Settings):
        self.settings = settings
        self._client = chromadb.PersistentClient(path=str(settings.chroma_rag_path))
        self._collection_name = "support_kb"
        self._collection = self._client.get_or_create_collection(name=self._collection_name)
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size = settings.rag_chunk_size,
            chunk_overlap = settings.rag_chunk_overlap,
            separators = [
                "\n\n",
                "\n",
                " ",
            ],
        )
    
    def ingest_directory(self,directory:Path,clear_existing:bool = False) -> dict[str,int]:
        if clear_existing:
            self._client.delete_collection(name=self._collection_name)
            self._collection = self._client.get_or_create_collection(name=self._collection_name)
        source_files = sorted([
            *directory.glob("*.md"),
            *directory.glob("*.txt"),
        ])
        docs:    list[str] = []
        metadatas:list[dict[str,Any]] = []
        ids:     list[str] = []

        for file_path in source_files:
            text = file_path.read_text(encoding="utf-8")
            chunks = self._splitter.split_text(text)
            
            for index,chunk in enumerate(chunks):
                chunk_hash = hashlib.sha1(chunk.encode("utf-8")).hexdigest()[:10]
                doc_id = f"{file_path.stem}-{index}-{chunk_hash}"
                docs.append(chunk)
                ids.append(doc_id)
                metadatas.append(
                    {
                        "source": file_path.name,
                        "chunk_index": index,
                    }
                )
        if docs:
            self._collection.upsert(ids=ids,documents=docs,metadatas=metadatas)
        
        return {
            "files_indexed": len(source_files),
            "chunks_indexed": len(docs),
            "collection_count": self._collection.count(),
        }


    def search(self,query:str,top_k:int|None=None) -> list[dict[str,Any]]:
        results = self._collection.query(
            query_texts=[query],
            n_results=top_k or self.settings.rag_top_k,
            include=["documents","distances","metadatas"],
        )
        documents = (results.get("documents") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]

        combined : list[dict[str,Any]] = []
        for i,document in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else None
            combined.append(
                {
                    "content":document,
                    "source":metadata.get("source","unknown") ,
                    "distance":distance,
                }
            )
        return combined
        
        
        
















# class ChromaKnowledgeBase:
#     """ChromaDB-backed Knowledge Base for RAG retrieval."""

#     def __init__(
#         self,
#         settings: Settings | None = None,
#         collection_name: str = "support_knowledge_base",
#     ) -> None:
#         self.settings: Settings = settings or get_settings()
#         self.collection_name = collection_name
#         self.chroma_path = str(self.settings.chroma_rag_path)
#         self.client = chromadb.PersistentClient(path=self.chroma_path)
#         self.collection: Collection = self.client.get_or_create_collection(
#             name=self.collection_name
#         )

#     def count(self) -> int:
#         """Return the number of items stored in the knowledge base collection."""
#         return self.collection.count()

#     def clear(self) -> None:
#         """Clear all records from the collection."""
#         self.client.delete_collection(name=self.collection_name)
#         self.collection = self.client.get_or_create_collection(name=self.collection_name)

#     def ingest_directory(
#         self,
#         dir_path: Path | str | None = None,
#         clear_existing: bool = False,
#     ) -> dict[str, int]:
#         """Read .md and .txt files from the directory, split them into chunks, and upsert them into ChromaDB."""
#         if clear_existing:
#             self.clear()

#         target_dir = Path(dir_path) if dir_path else self.settings.knowledge_base_path
#         if not target_dir.exists():
#             return {
#                 "files_indexed": 0,
#                 "chunks_indexed": 0,
#                 "collection_count": self.collection.count(),
#             }

#         splitter = RecursiveCharacterTextSplitter(
#             chunk_size=self.settings.rag_chunk_size,
#             chunk_overlap=self.settings.rag_chunk_overlap,
#         )

#         all_files = sorted(
#             [
#                 f
#                 for f in target_dir.iterdir()
#                 if f.is_file() and f.suffix.lower() in {".md", ".txt"}
#             ]
#         )

#         documents: list[str] = []
#         metadatas: list[dict[str, Any]] = []
#         ids: list[str] = []

#         files_indexed = 0
#         for file_path in all_files:
#             try:
#                 content = file_path.read_text(encoding="utf-8").strip()
#             except Exception:
#                 continue

#             if not content:
#                 continue

#             chunks = splitter.split_text(content)
#             if not chunks:
#                 continue

#             files_indexed += 1
#             for idx, chunk in enumerate(chunks):
#                 chunk_id = hashlib.sha256(
#                     f"{file_path.name}:{idx}:{chunk[:30]}".encode("utf-8")
#                 ).hexdigest()[:16]

#                 documents.append(chunk)
#                 metadatas.append(
#                     {
#                         "source": file_path.name,
#                         "file_path": str(file_path),
#                         "chunk_index": idx,
#                     }
#                 )
#                 ids.append(chunk_id)

#         chunks_indexed = len(documents)
#         if chunks_indexed > 0:
#             # Batch upsert to ChromaDB in chunks of 100
#             batch_size = 100
#             for i in range(0, chunks_indexed, batch_size):
#                 batch_docs = documents[i : i + batch_size]
#                 batch_metas = metadatas[i : i + batch_size]
#                 batch_ids = ids[i : i + batch_size]
#                 self.collection.upsert(
#                     ids=batch_ids,
#                     documents=batch_docs,
#                     metadatas=batch_metas,
#                 )

#         return {
#             "files_indexed": files_indexed,
#             "chunks_indexed": chunks_indexed,
#             "collection_count": self.collection.count(),
#         }

#     def search(
#         self,
#         query: str,
#         top_k: int | None = None,
#     ) -> list[dict[str, Any]]:
#         """Perform semantic search against the knowledge base."""
#         k = top_k or self.settings.rag_top_k
#         total_items = self.collection.count()
#         if total_items == 0 or not query.strip():
#             return []

#         n_results = min(k, total_items)
#         results = self.collection.query(
#             query_texts=[query],
#             n_results=n_results,
#         )

#         hits: list[dict[str, Any]] = []
#         if not results or not results.get("documents") or not results["documents"][0]:
#             return hits

#         docs = results["documents"][0]
#         metas = (
#             results.get("metadatas", [[]])[0]
#             if results.get("metadatas")
#             else [{}] * len(docs)
#         )
#         distances = (
#             results.get("distances", [[]])[0]
#             if results.get("distances")
#             else [None] * len(docs)
#         )

#         for doc, meta, dist in zip(docs, metas, distances):
#             metadata_dict = meta if isinstance(meta, dict) else {}
#             hits.append(
#                 {
#                     "content": doc,
#                     "metadata": metadata_dict,
#                     "distance": dist,
#                     "source": metadata_dict.get("source", "knowledge_base"),
#                 }
#             )

#         return hits
