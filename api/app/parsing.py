"""Turn an uploaded file into (page, text) sections."""

import io
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PyPdfError

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


class UnsupportedDocument(ValueError):
    """The message is safe to show to the end user."""


@dataclass
class Section:
    page: int | None
    text: str


def _parse_pdf(data: bytes) -> list[Section]:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise UnsupportedDocument("Ce PDF est protégé par un mot de passe.")
        sections = [
            Section(page=number, text=(page.extract_text() or "").strip())
            for number, page in enumerate(reader.pages, start=1)
        ]
    except (PyPdfError, ValueError, KeyError) as exc:
        if isinstance(exc, UnsupportedDocument):
            raise
        raise UnsupportedDocument("Ce PDF est illisible ou endommagé.") from exc
    return [s for s in sections if s.text]


def _parse_text(data: bytes) -> list[Section]:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return [Section(page=None, text=data.decode(encoding))]
        except UnicodeDecodeError:
            continue
    raise UnsupportedDocument("L'encodage de ce fichier texte n'est pas reconnu.")


def parse_document(filename: str, data: bytes) -> list[Section]:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise UnsupportedDocument(
            "Format non pris en charge. Utilisez un fichier PDF, TXT ou MD."
        )
    if not data:
        raise UnsupportedDocument("Ce fichier est vide.")
    sections = _parse_pdf(data) if extension == ".pdf" else _parse_text(data)
    if not any(s.text.strip() for s in sections):
        raise UnsupportedDocument(
            "Aucun texte trouvé. Un PDF numérisé doit d'abord passer par une "
            "reconnaissance de caractères (OCR)."
        )
    return sections
