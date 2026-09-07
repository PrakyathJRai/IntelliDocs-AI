from fastapi import FastAPI

from app.database import Base, engine
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.routes.documents import router as documents_router
from app.routes.search import router as search_router
from app.routes.chat import router as chat_router
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from fastapi.middleware.cors import CORSMiddleware
from app.models.user import User
from app.routes.auth import router as auth_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="IntelliDocs AI",
    description="AI-powered Document Intelligence and RAG Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(auth_router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to IntelliDocs AI",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "IntelliDocs AI"
    }