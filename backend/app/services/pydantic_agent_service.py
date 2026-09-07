from dataclasses import dataclass

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart,
)
from sqlalchemy.orm import Session

from app.services.agent_tools import search_documents_tool
from app.services.llm_service import LLM_API_KEY, LLM_MODEL


# ---------------------------------------------------------
# Structured output models
# ---------------------------------------------------------

class DocumentSource(BaseModel):
    document_id: int
    chunk_id: int
    chunk_index: int


class DocumentAnswer(BaseModel):
    answer: str
    sources: list[DocumentSource]


# ---------------------------------------------------------
# Agent dependencies
# ---------------------------------------------------------

@dataclass
class PydanticAgentDeps:
    db: Session
    user_id: int
    top_k: int = 5

# ---------------------------------------------------------
# Google Gemini model
# ---------------------------------------------------------

provider = GoogleProvider(
    api_key=LLM_API_KEY
)

model = GoogleModel(
    model_name=LLM_MODEL,
    provider=provider
)


# ---------------------------------------------------------
# Pydantic AI agent
# ---------------------------------------------------------

agent = Agent(
    model=model,
    output_type=DocumentAnswer,
    deps_type=PydanticAgentDeps,
    instructions="""
You are IntelliDocs AI, an intelligent document
question-answering assistant.

Your job is to answer questions using the user's
uploaded documents.

Rules:

1. Use the search_documents tool whenever the
   question requires information from uploaded
   documents.

2. Retrieved document information is the primary
   source of factual answers.

3. Do not invent facts that are not supported by
   retrieved documents.

4. If the required information cannot be found,
   clearly say that you could not find the answer
   in the provided documents.

5. Give clear and concise answers.

6. Return the answer and the relevant document
   sources.

7. When using document search, include the document
   source metadata returned by the search tool in
   the final sources field.
"""
)


# ---------------------------------------------------------
# Document search tool
# ---------------------------------------------------------

@agent.tool
def search_documents(
    ctx: RunContext[PydanticAgentDeps],
    query: str
) -> dict:
    """
    Search uploaded documents using semantic similarity.
    """

    return search_documents_tool(
        db=ctx.deps.db,
        user_id=ctx.deps.user_id,
        query=query,
        top_k=ctx.deps.top_k
)


# ---------------------------------------------------------
# Conversation history converter
# ---------------------------------------------------------

def build_message_history(
    messages
) -> list[ModelMessage]:
    """
    Convert application ChatMessage records into
    Pydantic AI message history.
    """

    history: list[ModelMessage] = []

    for message in messages:

        if message.role == "user":
            history.append(
                ModelRequest(
                    parts=[
                        UserPromptPart(
                            content=message.content
                        )
                    ]
                )
            )

        elif message.role == "assistant":
            history.append(
                ModelResponse(
                    parts=[
                        TextPart(
                            content=message.content
                        )
                    ],
                    model_name=LLM_MODEL
                )
            )

    return history


# ---------------------------------------------------------
# Agent execution
# ---------------------------------------------------------

async def run_pydantic_agent(
    db: Session,
    user_id: int,
    question: str,
    top_k: int = 5,
    message_history: list[ModelMessage] | None = None
) -> DocumentAnswer:

    deps = PydanticAgentDeps(
        db=db,
        user_id=user_id,
        top_k=top_k
)

    result = await agent.run(
        question,
        deps=deps,
        message_history=message_history or []
    )

    return result.output