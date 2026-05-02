"""
Semantic product search using Gemini text embeddings.

Embeds the full product catalog at startup into an in-memory index.
At query time, embeds the user's intent and returns the top-k most
relevant products via cosine similarity.

This replaces sending the full 130-product catalog (12K tokens) in every
context window -- instead, only the ~10-20 relevant products are included.
"""

import numpy as np
from typing import List, Dict, Optional
from ...logger import logger


_embedding_cache: Optional[Dict] = None


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _get_embedding(texts: List[str]) -> List[List[float]]:
    """Get text embeddings from Gemini with retry."""
    from google import genai
    from ...retry import vertex_ai_retry

    client = genai.Client()
    result = client.models.embed_content(
        model="text-embedding-005",
        contents=texts,
    )
    return [e.values for e in result.embeddings]


def _build_product_text(product: dict) -> str:
    """Build a searchable text representation of a product."""
    parts = [
        product.get("name", ""),
        product.get("category", ""),
        product.get("subcategory", ""),
        " ".join(product.get("style_tags", [])),
        " ".join(product.get("color_palette", [])),
        " ".join(product.get("room_compatibility", [])),
    ]
    if product.get("age_appropriate"):
        parts.append(" ".join(product["age_appropriate"]))
    return " ".join(p for p in parts if p)


def build_index(products: List[dict]) -> None:
    """Pre-compute embeddings for all products at startup."""
    global _embedding_cache

    logger.info(f"[PRODUCT SEARCH] Building embedding index for {len(products)} products...")

    texts = [_build_product_text(p) for p in products]

    # Batch embed (API supports up to 2048 texts per call)
    batch_size = 100
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        embeddings = _get_embedding(batch)
        all_embeddings.extend(embeddings)

    _embedding_cache = {
        "products": products,
        "texts": texts,
        "embeddings": np.array(all_embeddings),
    }

    logger.info(
        f"[PRODUCT SEARCH] Index built: {len(products)} products, "
        f"embedding dim: {_embedding_cache['embeddings'].shape[1]}"
    )


def search_products(
    query: str,
    top_k: int = 20,
    category_filter: Optional[str] = None,
    min_score: float = 0.3,
) -> List[dict]:
    """Search products by semantic similarity to query.

    Args:
        query: Natural language query (e.g. "modern bedroom furniture for a child")
        top_k: Maximum number of results
        category_filter: Optional category filter (e.g. "Home Decor", "Furniture")
        min_score: Minimum similarity score to include

    Returns:
        List of matching products sorted by relevance, with a 'relevance_score' field added.
    """
    if _embedding_cache is None:
        logger.warning("[PRODUCT SEARCH] Index not built, returning empty results")
        return []

    query_embedding = np.array(_get_embedding([query])[0])
    products = _embedding_cache["products"]
    embeddings = _embedding_cache["embeddings"]

    # Compute similarities
    scores = []
    for i, product in enumerate(products):
        if category_filter and product.get("category") != category_filter:
            continue
        score = _cosine_similarity(query_embedding, embeddings[i])
        if score >= min_score:
            scores.append((i, score))

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    results = []
    for idx, score in scores[:top_k]:
        product = dict(products[idx])
        product["relevance_score"] = round(score, 4)
        results.append(product)

    logger.info(
        f"[PRODUCT SEARCH] Query: '{query[:60]}' -> {len(results)} results "
        f"(top score: {results[0]['relevance_score'] if results else 0})"
    )
    return results


def get_slim_catalog(
    intent: str,
    top_k: int = 25,
    include_categories: Optional[List[str]] = None,
) -> List[dict]:
    """Get a slim product catalog relevant to the user's intent.

    Used to reduce the context window from 130 products to ~20-25 relevant ones.

    Args:
        intent: The user's detected intent or request
        top_k: Max products to return
        include_categories: If set, only include these categories

    Returns:
        Slim list of product dicts with only essential fields.
    """
    results = search_products(query=intent, top_k=top_k, min_score=0.2)

    if include_categories:
        results = [p for p in results if p.get("category") in include_categories]

    # Return only essential fields to minimize tokens
    slim = []
    for p in results:
        slim.append(
            {
                "product_id": p["product_id"],
                "name": p["name"],
                "category": p.get("category", ""),
                "subcategory": p.get("subcategory", ""),
                "price": p["price"],
                "in_stock": p.get("in_stock", True),
                "image_url": p.get("image_url", ""),
                "style_tags": p.get("style_tags", []),
                "color_palette": p.get("color_palette", []),
            }
        )

    return slim
