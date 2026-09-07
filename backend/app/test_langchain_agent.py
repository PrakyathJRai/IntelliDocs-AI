from app.database import SessionLocal
from app.services.langchain_agent_service import create_langchain_agent


db = SessionLocal()

try:
    agent = create_langchain_agent(
        db=db,
        top_k=5
    )

    print("\n========== LANGCHAIN TOOL TEST ==========")

    graph = agent.get_graph()

    print("\nGraph nodes:")
    for node_name in graph.nodes:
        print(f"- {node_name}")

    print("\nAgent successfully contains a tools node.")

    # Inspect the underlying graph structure.
    print("\nGraph edges:")

    for edge in graph.edges:
        print(f"- {edge.source} -> {edge.target}")

finally:
    db.close()