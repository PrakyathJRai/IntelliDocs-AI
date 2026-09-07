from app.services.llm_service import generate_answer


question = "What is IntelliDocs AI?"

context = """
IntelliDocs AI is an AI-powered document intelligence and RAG assistant.
It can process documents and answer questions using retrieved information.
"""


answer = generate_answer(
    question=question,
    context=context
)


print("\nAI ANSWER:")
print(answer)