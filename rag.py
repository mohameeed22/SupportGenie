from __future__ import annotations

import logging
import re
from typing import Any

import config
from store_context import POLICIES, PRODUCTS

logger = logging.getLogger(__name__)

_EMBEDDING_DIM = 384
_COLLECTION = None


def _get_embedding(text: str) -> list[float]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.warning("sentence-transformers not installed, falling back to keyword search")
        return _keyword_embedding(text)

    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def _keyword_embedding(text: str) -> list[float]:
    import hashlib

    seed = hashlib.md5(text.encode()).hexdigest()
    return [float(int(seed[i : i + 2], 16)) / 255.0 for i in range(0, min(32, len(seed)), 2)]


def _build_documents() -> list[dict[str, Any]]:
    docs = []
    for p in PRODUCTS:
        content = (
            f"Product: {p['name']}. Category: {p['category']}. "
            f"Price: ${p['price']:.2f}. Stock: {'In Stock' if p['in_stock'] else 'Out of Stock'}. "
            f"Description: {p['description']}"
        )
        docs.append({"content": content, "metadata": {"type": "product", "id": p["id"], "name": p["name"]}})

    sections = re.split(r"\n\n+", POLICIES.strip())
    for sec in sections:
        sec = sec.strip()
        if sec:
            docs.append({"content": sec, "metadata": {"type": "policy"}})

    return docs


def _get_or_create_collection():
    global _COLLECTION
    if _COLLECTION is not None:
        return _COLLECTION

    try:
        import chromadb

        client = chromadb.Client(chromadb.Settings(anonymized_telemetry=False))
        coll_name = "novabuy_store"
        try:
            client.delete_collection(coll_name)
        except Exception:
            pass
        _COLLECTION = client.create_collection(coll_name, metadata={"hnsw:space": "cosine"})

        docs = _build_documents()
        if not docs:
            return _COLLECTION

        ids = [f"doc_{i}" for i in range(len(docs))]
        contents = [d["content"] for d in docs]
        metadatas = [d["metadata"] for d in docs]

        embeddings = [_get_embedding(c) for c in contents]
        _COLLECTION.add(ids=ids, embeddings=embeddings, documents=contents, metadatas=metadatas)
        logger.info("RAG collection initialized with %d documents", len(docs))
    except Exception as exc:
        logger.warning("ChromaDB init failed (%s), falling back to keyword search", exc)
        _COLLECTION = None

    return _COLLECTION


def search_products(query: str, top_k: int | None = None) -> list[dict[str, Any]]:
    if top_k is None:
        top_k = config.RAG_TOP_K
    query_emb = _get_embedding(query)
    coll = _get_or_create_collection()

    if coll is not None:
        try:
            results = coll.query(query_embeddings=[query_emb], n_results=min(top_k * 2, 20))
            out = []
            if results and results.get("metadatas"):
                for meta, doc, dist in zip(
                    results["metadatas"][0],
                    results["documents"][0],
                    results["distances"][0],
                ):
                    if meta.get("type") == "product":
                        product = _find_product_by_id(meta.get("id", ""))
                        if product:
                            out.append({**product, "_relevance": round(1 - dist, 3)})
                return out[:top_k]
        except Exception as exc:
            logger.warning("ChromaDB query failed (%s), falling back", exc)

    return _keyword_search_products(query, top_k)


def search_policies(query: str, top_k: int | None = None) -> list[str]:
    if top_k is None:
        top_k = config.RAG_TOP_K
    query_emb = _get_embedding(query)
    coll = _get_or_create_collection()

    if coll is not None:
        try:
            results = coll.query(query_embeddings=[query_emb], n_results=min(top_k * 2, 20))
            out = []
            if results and results.get("metadatas"):
                for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
                    if meta.get("type") == "policy":
                        out.append(doc)
                return out[:top_k]
        except Exception:
            pass

    return _keyword_search_policies(query, top_k)


def relevance_search(query: str, top_k: int | None = None) -> str:
    products = search_products(query, top_k)
    policies = search_policies(query, top_k)

    parts = []
    if products:
        parts.append("=== RELEVANT PRODUCTS ===")
        for p in products:
            stock = "In Stock" if p.get("in_stock") else "Out of Stock"
            parts.append(f"- {p['name']} | ${p['price']:.2f} | {stock}")
            parts.append(f"  {p['description']}")

    if policies:
        parts.append("=== RELEVANT POLICIES ===")
        for pol in policies:
            parts.append(pol)

    return "\n".join(parts) if parts else ""


def _find_product_by_id(product_id: str) -> dict | None:
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return None


def _keyword_search_products(query: str, top_k: int) -> list[dict]:
    tokens = query.lower().split()
    ranked = []
    for p in PRODUCTS:
        haystack = f"{p['name']} {p['category']} {p['description']}".lower()
        score = sum(5 if t in p["name"].lower() else 3 if t in p["category"].lower() else 1 for t in tokens if t in haystack)
        if score > 0:
            ranked.append((score, p))
    ranked.sort(key=lambda x: (x[0], x[1].get("in_stock", False)), reverse=True)
    return [p for _, p in ranked[:top_k]]


def _keyword_search_policies(query: str, top_k: int) -> list[str]:
    tokens = query.lower().split()
    sections = re.split(r"\n\n+", POLICIES.strip())
    ranked = []
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        score = sum(1 for t in tokens if t in sec.lower())
        if score > 0:
            ranked.append((score, sec))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in ranked[:top_k]]
