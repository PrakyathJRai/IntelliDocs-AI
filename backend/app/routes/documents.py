from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends
)
from pathlib import Path
from uuid import uuid4
import zipfile

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.dependencies import get_current_user
from app.services.document_service import extract_text
from app.services.chunking_service import chunk_text
from app.services.embedding_service import generate_embedding


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


# =========================================================
# Upload Configuration
# =========================================================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}

# Maximum allowed upload size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024


# =========================================================
# File Content Validation
# =========================================================

def validate_file_content(
    file_path: Path,
    file_extension: str
):
    """
    Validate that the actual file content matches
    the expected file type.
    """

    # -----------------------------------------------------
    # PDF validation
    # -----------------------------------------------------

    if file_extension == ".pdf":

        with file_path.open("rb") as file:
            signature = file.read(4)

        if signature != b"%PDF":
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid PDF."
            )

    # -----------------------------------------------------
    # DOCX validation
    # -----------------------------------------------------

    elif file_extension == ".docx":

        if not zipfile.is_zipfile(file_path):
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid DOCX document."
            )

        try:

            with zipfile.ZipFile(
                file_path,
                "r"
            ) as archive:

                required_files = {
                    "[Content_Types].xml",
                    "word/document.xml"
                }

                archive_files = set(
                    archive.namelist()
                )

                missing_files = (
                    required_files - archive_files
                )

                if missing_files:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "The uploaded file is not "
                            "a valid DOCX document."
                        )
                    )

        except zipfile.BadZipFile:

            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid DOCX document."
            )

    # -----------------------------------------------------
    # TXT validation
    # -----------------------------------------------------

    elif file_extension == ".txt":

        try:

            with file_path.open(
                "r",
                encoding="utf-8"
            ) as file:

                file.read()

        except UnicodeDecodeError:

            raise HTTPException(
                status_code=400,
                detail="The uploaded TXT file is not valid UTF-8 text."
            )


# =========================================================
# Upload Document
# =========================================================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload, validate, process, chunk and embed
    a document for the authenticated user.
    """

    # -----------------------------------------------------
    # Validate filename
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="A valid filename is required."
        )

    # -----------------------------------------------------
    # Sanitize original filename
    # -----------------------------------------------------

    original_filename = Path(
        file.filename
    ).name

    # -----------------------------------------------------
    # Validate extension
    # -----------------------------------------------------

    file_extension = Path(
        original_filename
    ).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX and TXT files are supported."
        )

    # -----------------------------------------------------
    # Generate secure unique storage filename
    # -----------------------------------------------------

    stored_filename = (
        f"{uuid4().hex}{file_extension}"
    )

    file_path = (
        UPLOAD_DIR / stored_filename
    )

    # -----------------------------------------------------
    # Save uploaded file with size limit
    # -----------------------------------------------------

    try:

        total_size = 0

        with file_path.open("wb") as buffer:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                total_size += len(chunk)

                # -----------------------------------------
                # Enforce maximum file size
                # -----------------------------------------

                if total_size > MAX_FILE_SIZE:

                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "File size exceeds "
                            "the 10 MB limit."
                        )
                    )

                buffer.write(chunk)

    except HTTPException:

        # Remove partially uploaded file
        file_path.unlink(
            missing_ok=True
        )

        raise

    except Exception as exc:

        # Remove partially uploaded file
        file_path.unlink(
            missing_ok=True
        )

        print(
            f"FILE SAVE ERROR: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to save uploaded file."
        ) from exc

    # -----------------------------------------------------
    # Validate, process and store document
    # -----------------------------------------------------

    try:

        # -------------------------------------------------
        # Validate actual file content
        # -------------------------------------------------

        validate_file_content(
            file_path=file_path,
            file_extension=file_extension
        )

        # -------------------------------------------------
        # Extract text
        # -------------------------------------------------

        text = extract_text(
            str(file_path)
        )

        # -------------------------------------------------
        # Validate extracted text
        # -------------------------------------------------

        if not text.strip():

            raise HTTPException(
                status_code=400,
                detail=(
                    "The uploaded document "
                    "contains no readable text."
                )
            )

        # -------------------------------------------------
        # Chunk text
        # -------------------------------------------------

        chunks = chunk_text(
            text
        )

        if not chunks:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No usable text chunks "
                    "were created."
                )
            )

        # -------------------------------------------------
        # Create document
        # -------------------------------------------------

        document = Document(
            user_id=current_user.id,
            filename=original_filename,
            file_type=file_extension,
            file_path=str(file_path)
        )

        db.add(
            document
        )

        # Generate document ID
        db.flush()

        # -------------------------------------------------
        # Generate embeddings
        # -------------------------------------------------

        for index, chunk in enumerate(chunks):

            embedding = generate_embedding(
                chunk
            )

            document_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk,
                embedding=embedding
            )

            db.add(
                document_chunk
            )

        # -------------------------------------------------
        # Commit database transaction
        # -------------------------------------------------

        db.commit()

        db.refresh(
            document
        )

    except HTTPException:

        db.rollback()

        # Remove uploaded file
        try:

            file_path.unlink(
                missing_ok=True
            )

        except Exception:
            pass

        raise

    except Exception as exc:

        db.rollback()

        # Remove uploaded file if processing fails
        try:

            file_path.unlink(
                missing_ok=True
            )

        except Exception:
            pass

        print(
            f"DOCUMENT UPLOAD ERROR: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process document."
        ) from exc

    # -----------------------------------------------------
    # Upload response
    # -----------------------------------------------------

    return {
        "message": (
            "Document uploaded, processed and "
            "embedded successfully"
        ),
        "document_id": document.id,
        "filename": document.filename,
        "file_type": document.file_type,
        "text_length": len(text),
        "chunk_count": len(chunks),
        "chunks": chunks
    }


# =========================================================
# Get User Documents
# =========================================================

@router.get("/")
async def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return only documents belonging to
    the authenticated user.
    """

    documents = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id
        )
        .order_by(
            Document.created_at.desc()
        )
        .all()
    )

    results = []

    for document in documents:

        chunk_count = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == document.id
            )
            .count()
        )

        results.append({
            "document_id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "text_length": None,
            "chunk_count": chunk_count,
            "created_at": document.created_at
        })

    return results


# =========================================================
# Delete Document
# =========================================================

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a document belonging to the authenticated user.

    The document's chunks and stored file are also removed.
    """

    # -----------------------------------------------------
    # Find document owned by current user
    # -----------------------------------------------------

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
        .first()
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # -----------------------------------------------------
    # Save file path before deleting database record
    # -----------------------------------------------------

    file_path = Path(
        document.file_path
    )

    try:

        # -------------------------------------------------
        # Delete document chunks
        # -------------------------------------------------

        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document.id
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # Delete document
        # -------------------------------------------------

        db.delete(
            document
        )

        db.commit()

        # -------------------------------------------------
        # Delete physical file
        # -------------------------------------------------

        try:

            file_path.unlink(
                missing_ok=True
            )

        except Exception as file_error:

            print(
                "FILE DELETE WARNING: "
                f"{type(file_error).__name__}: "
                f"{file_error}"
            )

    except Exception as exc:

        db.rollback()

        print(
            f"DOCUMENT DELETE ERROR: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to delete document."
        ) from exc

    # -----------------------------------------------------
    # Delete response
    # -----------------------------------------------------

    return {
        "message": "Document deleted successfully",
        "document_id": document_id
    }