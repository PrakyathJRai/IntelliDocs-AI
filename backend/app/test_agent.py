from app.database import SessionLocal
from app.services.agent_service import run_agent


db = SessionLocal()

try:
    result = run_agent(
        db=db,
        question="What is IntelliDocs AI?",
        top_k=5
    )

    print("\n========== AGENT RESULT ==========")
    print("Question:", result["question"])
    print("Answer:", result["answer"])
    print("Tool Calls:", result["tool_calls"])

finally:
    db.close()