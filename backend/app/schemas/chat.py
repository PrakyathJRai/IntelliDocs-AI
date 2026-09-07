from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    top_k: int = 5
    session_id: int | None = None