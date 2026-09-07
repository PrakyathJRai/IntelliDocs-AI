from app.database import SessionLocal
from app.services.agent_tools import search_documents_tool


db = SessionLocal()

try:
    query = "What is IntelliDocs AI?"

    result = search_documents_tool(
        db=db,
        query=query,
        top_k=5
    )

    print("\n========== DOCUMENT SEARCH TOOL TEST ==========")
    print("Query:", query)
    print("Number of results:", len(result["results"]))

    print("\n========== RETRIEVED DOCUMENTS ==========")

    for item in result["results"]:
        print("\nDocument ID:", item["document_id"])
        print("Chunk ID:", item["chunk_id"])
        print("Chunk Index:", item["chunk_index"])
        print("Content:")
        print(item["content"])

    print("\n========== SOURCES ==========")

    for source in result["sources"]:
        print(source)

finally:
    db.close()