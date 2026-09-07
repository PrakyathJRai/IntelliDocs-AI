from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import generate_embedding


# Maximum acceptable cosine distance.
# Lower distance = higher semantic similarity.
#
# 0.65 means:
# cosine similarity must be approximately >= 0.35
#
# Chunks with a larger distance are treated as
# insufficiently relevant to the user's question.
SIMILARITY_DISTANCE_THRESHOLD = 0.55


def semantic_search(
    db: Session,
    query: str,
    user_id: int,
    top_k: int = 5
):
    """
    Search the authenticated user's document chunks
    using semantic similarity.

    Only sufficiently relevant chunks are returned.
    """

    query_embedding = generate_embedding(query)

    distance = DocumentChunk.embedding.cosine_distance(
        query_embedding
    )

    statement = (
        select(DocumentChunk)
        .join(
            Document,
            Document.id == DocumentChunk.document_id
        )
        .where(
            Document.user_id == user_id,
            DocumentChunk.embedding.is_not(None),
            distance <= SIMILARITY_DISTANCE_THRESHOLD
        )
        .order_by(distance)
        .limit(top_k)
    )

    results = db.execute(
        statement
    ).scalars().all()

    return results