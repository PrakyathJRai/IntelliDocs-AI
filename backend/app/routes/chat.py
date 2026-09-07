import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import ChatRequest
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.dependencies import get_current_user
from app.services.langchain_chat_service import run_langchain_chat


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# =========================================================
# Main LangChain / LangGraph Chat Endpoint
# =========================================================

@router.post("/")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Chat with the IntelliDocs AI LangChain/LangGraph agent.

    Creates a new chat session for the authenticated user
    when session_id is not provided.

    Existing sessions can only be accessed by their owner.
    """

    # ---------------------------------------------------------
    # 1. Create or retrieve chat session
    # ---------------------------------------------------------

    if request.session_id is None:

        session = ChatSession(
            user_id=current_user.id
        )

        db.add(session)
        db.commit()
        db.refresh(session)

    else:

        session = (
            db.query(ChatSession)
            .filter(
                ChatSession.id == request.session_id,
                ChatSession.user_id == current_user.id
            )
            .first()
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )

    # ---------------------------------------------------------
    # 2. Run LangChain / LangGraph agent
    # ---------------------------------------------------------

    try:

        result = run_langchain_chat(
            db=db,
            user_id=current_user.id,
            question=request.question,
            session_id=session.id,
            top_k=request.top_k
        )

    except Exception as exc:

        db.rollback()

        print(
            f"CHAT ERROR: {type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "AI service is temporarily unavailable. "
                "Please try again later."
            )
        ) from exc

    # ---------------------------------------------------------
    # 3. Save user message
    # ---------------------------------------------------------

    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=request.question
    )

    db.add(user_message)

    # ---------------------------------------------------------
    # 4. Save assistant message + sources
    # ---------------------------------------------------------

    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=result["answer"],
        sources=json.dumps(
            result.get("sources", [])
        )
    )

    db.add(assistant_message)

    # ---------------------------------------------------------
    # 5. Commit conversation
    # ---------------------------------------------------------

    db.commit()

    # ---------------------------------------------------------
    # 6. Return response
    # ---------------------------------------------------------

    return {
        "session_id": session.id,
        "question": request.question,
        "answer": result["answer"],
        "sources": result.get("sources", [])
    }


# =========================================================
# Get Chat Sessions
# =========================================================

@router.get("/sessions/")
async def get_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return only chat sessions belonging to the authenticated user.

    Sessions are ordered from newest to oldest.
    """

    sessions = (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == current_user.id
        )
        .order_by(
            ChatSession.created_at.desc(),
            ChatSession.id.desc()
        )
        .all()
    )

    results = []

    for session in sessions:

        messages = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session.id
            )
            .order_by(
                ChatMessage.created_at.asc(),
                ChatMessage.id.asc()
            )
            .all()
        )

        message_count = len(messages)

        first_user_message = next(
            (
                message.content
                for message in messages
                if message.role == "user"
            ),
            None
        )

        if first_user_message:

            title = first_user_message.strip()

            if len(title) > 45:
                title = title[:45].rstrip() + "..."

        else:

            title = "New conversation"

        results.append({
            "session_id": session.id,
            "title": title,
            "created_at": session.created_at,
            "message_count": message_count
        })

    return results


# =========================================================
# Get Messages For A Chat Session
# =========================================================

@router.get("/sessions/{session_id}/messages")
async def get_chat_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return all messages belonging to a chat session
    owned by the authenticated user.
    """

    # ---------------------------------------------------------
    # 1. Verify session belongs to current user
    # ---------------------------------------------------------

    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Chat session not found"
        )

    # ---------------------------------------------------------
    # 2. Load messages
    # ---------------------------------------------------------

    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id
        )
        .order_by(
            ChatMessage.created_at.asc(),
            ChatMessage.id.asc()
        )
        .all()
    )

    # ---------------------------------------------------------
    # 3. Build response
    # ---------------------------------------------------------

    results = []

    for message in messages:

        sources = []

        if message.sources:

            try:

                parsed_sources = json.loads(
                    message.sources
                )

                if isinstance(parsed_sources, list):
                    sources = parsed_sources

            except (
                json.JSONDecodeError,
                TypeError
            ):

                sources = []

        results.append({
            "message_id": message.id,
            "session_id": message.session_id,
            "role": message.role,
            "content": message.content,
            "sources": sources,
            "created_at": message.created_at
        })

    return results


# =========================================================
# Pydantic AI Chat Endpoint
# =========================================================

@router.post("/pydantic")
async def pydantic_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Chat with the IntelliDocs AI Pydantic AI agent.

    Creates a new chat session for the authenticated user
    when session_id is not provided.

    Existing sessions can only be accessed by their owner.
    """

    from app.services.pydantic_agent_service import (
        run_pydantic_agent,
        build_message_history
    )

    # ---------------------------------------------------------
    # 1. Create or retrieve chat session
    # ---------------------------------------------------------

    if request.session_id is None:

        session = ChatSession(
            user_id=current_user.id
        )

        db.add(session)
        db.commit()
        db.refresh(session)

    else:

        session = (
            db.query(ChatSession)
            .filter(
                ChatSession.id == request.session_id,
                ChatSession.user_id == current_user.id
            )
            .first()
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )

    # ---------------------------------------------------------
    # 2. Load previous conversation
    # ---------------------------------------------------------

    previous_messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session.id
        )
        .order_by(
            ChatMessage.created_at.asc(),
            ChatMessage.id.asc()
        )
        .all()
    )

    message_history = build_message_history(
        previous_messages
    )

    # ---------------------------------------------------------
    # 3. Run Pydantic AI agent
    # ---------------------------------------------------------

    try:

        result = await run_pydantic_agent(
            db=db,
            user_id=current_user.id,
            question=request.question,
            top_k=request.top_k,
            message_history=message_history
        )

    except Exception as exc:

        db.rollback()

        print(
            f"PYDANTIC CHAT ERROR: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "AI service is temporarily unavailable. "
                "Please try again later."
            )
        ) from exc

    # ---------------------------------------------------------
    # 4. Save user message
    # ---------------------------------------------------------

    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=request.question
    )

    db.add(user_message)

    # ---------------------------------------------------------
    # 5. Save assistant message + sources
    # ---------------------------------------------------------

    pydantic_sources = [
        source.model_dump()
        for source in result.sources
    ]

    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=result.answer,
        sources=json.dumps(
            pydantic_sources
        )
    )

    db.add(assistant_message)

    # ---------------------------------------------------------
    # 6. Commit conversation
    # ---------------------------------------------------------

    db.commit()

    # ---------------------------------------------------------
    # 7. Return response
    # ---------------------------------------------------------

    return {
        "session_id": session.id,
        "question": request.question,
        "answer": result.answer,
        "sources": pydantic_sources
    }