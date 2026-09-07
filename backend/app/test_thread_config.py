from app.database import SessionLocal
from app.models.chat_session import ChatSession


db = SessionLocal()

try:
    print("\n========== LANGGRAPH THREAD TEST ==========")

    session = (
        db.query(ChatSession)
        .order_by(ChatSession.id.asc())
        .first()
    )

    if session is None:
        print("No chat sessions found.")
    else:
        thread_id = str(session.id)

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        print("Chat session ID:", session.id)
        print("LangGraph thread ID:", thread_id)
        print("Configuration:", config)

        print("\nLangGraph thread configuration created successfully.")

finally:
    db.close()