from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship

from app.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    session_id = Column(
        Integer,
        ForeignKey(
            "chat_sessions.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    role = Column(
        String(20),
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    # JSON-serialized document source metadata.
    # Example:
    # [
    #   {
    #     "document_id": 7,
    #     "chunk_id": 12,
    #     "chunk_index": 0
    #   }
    # ]
    sources = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    session = relationship(
        "ChatSession",
        back_populates="messages"
    )