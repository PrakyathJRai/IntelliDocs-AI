import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.7-flash")

if not LLM_API_KEY:
    raise ValueError("LLM_API_KEY is not configured")

client = genai.Client(api_key=LLM_API_KEY)


def generate_answer(
    question: str,
    context: str,
    conversation_history: str = ""
) -> str:

    prompt = f"""
You are IntelliDocs AI, an intelligent document question-answering assistant.

Your job is to answer the user's question using the provided document context.

You may also use the previous conversation history to understand references,
follow-up questions, and conversational context.

IMPORTANT RULES:

1. Use the document context as the primary source of factual information.
2. Use conversation history only to understand the user's intent and references.
3. Do not invent information that is not supported by the document context.
4. If the answer cannot be found in the provided documents, say:
"I could not find the answer in the provided documents."
5. Answer clearly and concisely.

Previous conversation:
{conversation_history if conversation_history else "No previous conversation."}

Document context:
{context}

Current user question:
{question}
"""

    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt
    )

    return response.text