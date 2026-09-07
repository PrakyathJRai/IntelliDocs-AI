import os

import psycopg
from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver


load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://intellidocs_user:intellidocs_password@localhost:5433/intellidocs"
)


def get_psycopg_connection():
    """
    Create a psycopg connection for LangGraph checkpoint storage.

    SQLAlchemy uses the postgresql+psycopg:// URL format,
    while psycopg.connect() expects postgresql://.
    """

    psycopg_url = DATABASE_URL.replace(
        "postgresql+psycopg://",
        "postgresql://",
        1
    )

    return psycopg.connect(
        psycopg_url,
        autocommit=True
    )


def create_checkpointer():
    """
    Create a LangGraph PostgreSQL checkpointer.
    """

    connection = get_psycopg_connection()

    checkpointer = PostgresSaver(connection)

    return checkpointer, connection