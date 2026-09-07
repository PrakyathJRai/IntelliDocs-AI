from app.services.checkpoint_service import create_checkpointer


checkpointer, connection = create_checkpointer()

try:
    print("\n========== LANGGRAPH CHECKPOINT SETUP ==========")

    print("Running PostgreSQL checkpoint setup...")

    checkpointer.setup()

    print("LangGraph checkpoint tables initialized successfully.")

finally:
    connection.close()
    print("PostgreSQL connection closed.")