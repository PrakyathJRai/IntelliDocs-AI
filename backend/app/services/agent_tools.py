from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.search_service import semantic_search


def search_documents_tool(
    db: Session,
    user_id: int,
    query: str,
    top_k: int = 5
) -> dict:
    """
    Search only the authenticated user's documents.
    """

    results = semantic_search(
        db=db,
        query=query,
        user_id=user_id,
        top_k=top_k
    )

    if not results:
        return {
            "results": [],
            "sources": []
        }

    retrieved_results = []
    sources = []

    for chunk in results:

        document = (
            db.query(Document)
            .filter(
                Document.id == chunk.document_id,
                Document.user_id == user_id
            )
            .first()
        )

        filename = (
            document.filename
            if document is not None
            else f"Document #{chunk.document_id}"
        )

        retrieved_results.append({
            "document_id": chunk.document_id,
            "chunk_id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "filename": filename,
            "content": chunk.content
        })

        sources.append({
            "document_id": chunk.document_id,
            "chunk_id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "filename": filename
        })

    return {
        "results": retrieved_results,
        "sources": sources
    }