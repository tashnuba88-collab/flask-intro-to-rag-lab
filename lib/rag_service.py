from __future__ import annotations

import re
from typing import Any

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "get",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "me",
    "my",
    "need",
    "of",
    "on",
    "or",
    "our",
    "should",
    "so",
    "the",
    "their",
    "to",
    "use",
    "what",
    "when",
    "where",
    "who",
    "why",
    "with",
    "you",
    "your",
}


def tokenize(text: str) -> set[str]:
    """Convert text into a set of searchable lowercase tokens."""
    words = re.findall(r"[a-z0-9']+", text.lower())
    tokens = set()
    for word in words:
        word = word.strip("'")
        if len(word) <= 1:
            continue
        if word in STOPWORDS:
            continue
        tokens.add(word)
    return tokens


def document_search_text(document: dict[str, Any]) -> str:
    """Combine searchable document fields into one text value."""
    parts = [
        document["title"],
        document["category"],
        " ".join(document["tags"]),
        document["text"],
    ]
    return " ".join(parts)


def score_document(query: str, document: dict[str, Any]) -> dict[str, Any]:
    """Score a document using keyword overlap."""
    query_tokens = tokenize(query)
    document_tokens = tokenize(document_search_text(document))
    title_tokens = tokenize(document["title"])

    matched_terms = sorted(query_tokens & document_tokens)
    title_matches = query_tokens & title_tokens

    score = len(matched_terms) + 0.5 * len(title_matches)

    return {
        "document": document,
        "score": score,
        "matched_terms": matched_terms,
    }


def retrieve_context(
    query: str,
    documents: list[dict[str, Any]],
    limit: int = 2,
    minimum_score: float = 1.0,
) -> list[dict[str, Any]]:
    """Select the most relevant documents for the query."""
    scored = [score_document(query, document) for document in documents]
    relevant = [match for match in scored if match["score"] >= minimum_score]
    relevant.sort(key=lambda match: match["score"], reverse=True)
    return relevant[:limit]


def format_context(context_matches: list[dict[str, Any]]) -> str:
    """Format retrieved documents into a context block for the prompt."""
    if not context_matches:
        return "No relevant context was found in the approved company documents."

    blocks = []
    for match in context_matches:
        document = match["document"]
        blocks.append(
            f"Source ID: {document['id']}\n"
            f"Title: {document['title']}\n"
            f"Category: {document['category']}\n"
            f"Content: {document['text']}"
        )
    return "\n\n---\n\n".join(blocks)


def build_prompt(query: str, context_matches: list[dict[str, Any]]) -> str:
    """Build a structured prompt with instructions, context, question, and requirements."""
    context = format_context(context_matches)

    return (
        "Instructions:\n"
        "You are an internal documentation assistant. "
        "Use only the information in the Context section to answer the question. "
        "Do not invent policies, steps, numbers, or other details that are not "
        "in the Context.\n\n"
        "Context:\n"
        f"{context}\n\n"
        "Question:\n"
        f"{query}\n\n"
        "Response requirements:\n"
        "- Answer clearly and briefly.\n"
        "- Base the answer only on the provided context.\n"
        "- If the context does not contain enough information, say so.\n"
        "- Mention the Source ID of each document you rely on.\n"
    )


def source_metadata(match: dict[str, Any]) -> dict[str, str]:
    """Return source information that is safe to expose in the API response."""
    document = match["document"]
    return {
        "id": document["id"],
        "title": document["title"],
    }
