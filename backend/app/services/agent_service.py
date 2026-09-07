from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from app.models.chat_message import ChatMessage
from app.services.agent_tools import search_documents_tool
from app.services.llm_service import LLM_API_KEY, LLM_MODEL


client = genai.Client(api_key=LLM_API_KEY)


def run_agent(
    db: Session,
    question: str,
    top_k: int = 5,
    session_id: int | None = None
):
    """
    Run the IntelliDocs AI agent with conversation history
    and explicit Gemini tool calling.
    """

    # ---------------------------------------------------------
    # 1. Retrieve previous conversation
    # ---------------------------------------------------------

    conversation_history = ""

    if session_id is not None:

        messages = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session_id
            )
            .order_by(ChatMessage.id.asc())
            .all()
        )

        if messages:

            history_parts = []

            for message in messages:

                history_parts.append(
                    f"{message.role.upper()}: {message.content}"
                )

            conversation_history = "\n".join(
                history_parts
            )

    # ---------------------------------------------------------
    # 2. Define document-search tool
    # ---------------------------------------------------------

    search_tool = types.FunctionDeclaration(
        name="search_documents",
        description=(
            "Search the uploaded documents using semantic similarity "
            "to find information relevant to the user's question."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "query": types.Schema(
                    type=types.Type.STRING,
                    description=(
                        "A concise search query describing the "
                        "information needed from the documents."
                    ),
                ),
                "top_k": types.Schema(
                    type=types.Type.INTEGER,
                    description=(
                        "Maximum number of relevant document chunks "
                        "to retrieve."
                    ),
                ),
            },
            required=["query"],
        ),
    )

    tool = types.Tool(
        function_declarations=[search_tool]
    )

    # ---------------------------------------------------------
    # 3. Create Gemini agent
    # ---------------------------------------------------------

    system_instruction = """
You are IntelliDocs AI, an intelligent document question-answering assistant.

Your job is to answer questions using the user's uploaded documents.

Rules:

1. Use the search_documents tool when document information is needed.
2. Use previous conversation history to understand follow-up questions,
   references, and pronouns such as "it", "they", "this", or "that".
3. Retrieved document information is the primary source of factual answers.
4. Do not invent facts that are not supported by retrieved documents.
5. If the required information cannot be found, clearly say so.
6. Give clear and concise answers.
"""

    if conversation_history:

        system_instruction += f"""

Previous conversation:

{conversation_history}
"""

    chat = client.chats.create(
        model=LLM_MODEL,
        config=types.GenerateContentConfig(
            tools=[tool],
            system_instruction=system_instruction,
        ),
    )

    # ---------------------------------------------------------
    # 4. Send current question
    # ---------------------------------------------------------

    response = chat.send_message(question)

    tool_calls = []
    source_results = []

    # ---------------------------------------------------------
    # 5. Explicit tool-calling loop
    # ---------------------------------------------------------

    while True:

        function_calls = response.function_calls

        if not function_calls:
            break

        function_responses = []

        for function_call in function_calls:

            if function_call.name != "search_documents":
                continue

            args = function_call.args or {}

            query = args.get(
                "query",
                question
            )

            requested_top_k = args.get(
                "top_k",
                top_k
            )

            requested_top_k = max(
                1,
                min(int(requested_top_k), 10)
            )

            tool_calls.append(
                {
                    "tool": "search_documents",
                    "query": query,
                    "top_k": requested_top_k,
                }
            )

            # -------------------------------------------------
            # Execute ONE semantic search
            # -------------------------------------------------

            tool_result = search_documents_tool(
                db=db,
                query=query,
                top_k=requested_top_k
            )

            # -------------------------------------------------
            # Collect source metadata from same search
            # -------------------------------------------------

            source_results.extend(
                tool_result["sources"]
            )

            # -------------------------------------------------
            # Send retrieved content to Gemini
            # -------------------------------------------------

            function_responses.append(
                types.Part.from_function_response(
                    name="search_documents",
                    response={
                        "results": tool_result["results"]
                    },
                )
            )

        # Send tool results back to Gemini
        response = chat.send_message(
            function_responses
        )

    # ---------------------------------------------------------
    # 6. Remove duplicate sources
    # ---------------------------------------------------------

    unique_sources = []

    seen = set()

    for source in source_results:

        key = (
            source["document_id"],
            source["chunk_id"],
            source["chunk_index"],
        )

        if key not in seen:

            seen.add(key)

            unique_sources.append(source)

    # ---------------------------------------------------------
    # 7. Return final result
    # ---------------------------------------------------------

    return {
        "question": question,
        "answer": response.text,
        "sources": unique_sources,
        "tool_calls": tool_calls,
    }