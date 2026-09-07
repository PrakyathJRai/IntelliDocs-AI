from pathlib import Path
from pypdf import PdfReader
from docx import Document


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".txt":
        return path.read_text(encoding="utf-8")

    elif extension == ".pdf":
        reader = PdfReader(str(path))

        text = ""

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text

    elif extension == ".docx":
        document = Document(str(path))

        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

        return text

    else:
        raise ValueError("Unsupported file type")