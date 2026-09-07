from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.search_service import semantic_search


router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


@router.get("/")
async def search_documents(
    query: str,
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    results = semantic_search(
        db=db,
        query=query,
        top_k=top_k
    )

    return {
        "query": query,
        "result_count": len(results),
        "results": [
            {
                "document_id": result.document_id,
                "chunk_id": result.id,
                "chunk_index": result.chunk_index,
                "content": result.content
            }
            for result in results
        ]
    }