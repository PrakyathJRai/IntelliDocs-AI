from sqlalchemy.orm import Session

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from app.services.agent_tools import search_documents_tool
from app.services.llm_service import LLM_API_KEY, LLM_MODEL
from app.services.checkpoint_service import create_checkpointer


def create_langchain_agent(
    db: Session,
    user_id: int,
    top_k: int = 5
):
    """
    Create the IntelliDocs AI LangChain/LangGraph agent.

    The agent uses:
    - Gemini as the LLM
    - LangChain agent framework
    - LangGraph internally
    - PostgreSQL-backed checkpoint persistence
    - Existing pgvector document search
    """

    @tool
    def search_documents(query: str) -> dict:
        """
        Search uploaded documents using semantic similarity.

        Use this tool whenever the user's question requires
        information from the uploaded documents.
        """

        return search_documents_tool(
            db=db,
            user_id=user_id,
            query=query,
            top_k=top_k
        )

    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=LLM_API_KEY

    )

    checkpointer, connection = create_checkpointer()

    agent = create_agent(
        model=llm,
        tools=[search_documents],
        system_prompt="""
You are IntelliDocs AI, an intelligent document
question-answering assistant.

Your job is to answer questions using the user's
uploaded documents.

Rules:

1. Use the search_documents tool when document
   information is required.

2. Retrieved document information is the primary
   source of factual answers.

3. Do not invent facts that are not supported by
   retrieved documents.

4. If the required information cannot be found,
   clearly say that you could not find the answer
   in the provided documents.

5. Give clear, concise and useful answers.

6. Use the conversation state maintained by
   LangGraph to understand previous messages,
   follow-up questions, references and pronouns.
""",
        checkpointer=checkpointer
    )

    # Keep the PostgreSQL connection alive while
    # the LangGraph checkpointer is being used.
    agent._intellidocs_checkpoint_connection = connection

    return agent