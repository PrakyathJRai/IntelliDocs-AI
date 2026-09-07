import json

from sqlalchemy.orm import Session

from langchain.agents import create_agent

from app.services.langchain_agent_service import (
    create_langchain_agent
)


def run_langchain_chat(
    db: Session,
    user_id: int,
    question: str,
    session_id: int | None = None,
    top_k: int = 5
):

    agent = create_langchain_agent(
    db=db,
    user_id=user_id,
    top_k=top_k
)

    thread_id = (
        str(session_id)
        if session_id is not None
        else "default"
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    try:
        response = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            },
            config=config
        )

        messages = response.get(
            "messages",
            []
        )

        if not messages:
            return {
                "answer": "No response was generated.",
                "sources": [],
                "thread_id": thread_id
            }

        # -------------------------------------------------
        # Extract the final assistant response
        # -------------------------------------------------

        final_message = messages[-1]

        answer_content = final_message.content

        # LangChain may return structured content
        # instead of a simple string.
        if isinstance(answer_content, list):
            text_parts = []

            for part in answer_content:
                if isinstance(part, dict):
                    text = part.get("text")

                    if text:
                        text_parts.append(text)

                elif isinstance(part, str):
                    text_parts.append(part)

            answer_content = "\n".join(text_parts)

        if not isinstance(answer_content, str):
            answer_content = str(answer_content)

        # -------------------------------------------------
        # Extract document sources from tool messages
        # -------------------------------------------------

        sources = []

        for message in messages:

            # We only care about LangChain tool messages.
            if getattr(message, "type", None) != "tool":
                continue

            tool_output = getattr(
                message,
                "content",
                None
            )

            # ---------------------------------------------
            # Case 1: Tool output is already a dictionary
            # ---------------------------------------------

            if isinstance(tool_output, dict):

                tool_sources = tool_output.get(
                    "sources",
                    []
                )

                if isinstance(tool_sources, list):
                    sources.extend(tool_sources)

            # ---------------------------------------------
            # Case 2: Tool output is a JSON string
            # ---------------------------------------------

            elif isinstance(tool_output, str):

                try:
                    parsed_output = json.loads(
                        tool_output
                    )

                    if isinstance(
                        parsed_output,
                        dict
                    ):
                        tool_sources = (
                            parsed_output.get(
                                "sources",
                                []
                            )
                        )

                        if isinstance(
                            tool_sources,
                            list
                        ):
                            sources.extend(
                                tool_sources
                            )

                except json.JSONDecodeError:
                    # Ignore non-JSON tool output.
                    pass

        # -------------------------------------------------
        # Remove duplicate sources
        # -------------------------------------------------

        unique_sources = []
        seen = set()

        for source in sources:

            if not isinstance(source, dict):
                continue

            key = (
                source.get("document_id"),
                source.get("chunk_id"),
                source.get("chunk_index")
            )

            if key not in seen:

                seen.add(key)

                unique_sources.append(
                    source
                )

        # -------------------------------------------------
        # Return final result
        # -------------------------------------------------

        return {
            "answer": answer_content,
            "sources": unique_sources,
            "thread_id": thread_id
        }

    finally:

        # Close the PostgreSQL checkpoint connection
        # created for this agent invocation.
        connection = getattr(
            agent,
            "_intellidocs_checkpoint_connection",
            None
        )

        if connection is not None:
            connection.close()