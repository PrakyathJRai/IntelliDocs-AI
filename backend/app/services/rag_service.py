from sqlalchemy.orm import Session

from app.services.search_service import semantic_search
from app.services.llm_service import generate_answer
from app.models.chat_message import ChatMessage


def generate_rag_answer(
    db: Session,
    question: str,
    top_k: int = 5,
    session_id: int | None = None
):
    # Retrieve relevant document chunks
    results = semantic_search(
        db=db,
        query=question,
        top_k=top_k
    )

    if not results:
        return {
            "answer": "I could not find the answer in the provided documents.",
            "sources": []
        }

    # Build document context
    context_parts = []

    for result in results:
        context_parts.append(
            f"Document ID: {result.document_id}\n"
            f"Chunk ID: {result.id}\n"
            f"Content:\n{result.content}"
        )

    context = "\n\n---\n\n".join(context_parts)

    # Retrieve previous conversation messages
    conversation_history = ""

    if session_id is not None:
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

        if messages:
            history_parts = []

            for message in messages:
                history_parts.append(
                    f"{message.role.upper()}: {message.content}"
                )

            conversation_history = "\n".join(history_parts)

    # Generate answer using RAG + conversation history
    answer = generate_answer(
        question=question,
        context=context,
        conversation_history=conversation_history
    )

    sources = [
        {
            "document_id": result.document_id,
            "chunk_id": result.id,
            "chunk_index": result.chunk_index
        }
        for result in results
    ]

    return {
        "answer": answer,
        "sources": sources
    }