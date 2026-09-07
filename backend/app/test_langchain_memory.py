from app.database import SessionLocal
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage


db = SessionLocal()

try:
    print("\n========== LANGCHAIN MEMORY TEST ==========")

    sessions = (
        db.query(ChatSession)
        .order_by(ChatSession.id.asc())
        .all()
    )

    print(f"\nTotal chat sessions: {len(sessions)}")

    for session in sessions:
        print(f"\n--- Session {session.id} ---")

        messages = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session.id
            )
            .order_by(ChatMessage.id.asc())
            .all()
        )

        print(f"Messages: {len(messages)}")

        for message in messages:
            role = "human" if message.role == "user" else "ai"

            print(f"{role.upper()}: {message.content}")

finally:
    db.close()