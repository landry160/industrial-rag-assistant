"""Paragraph-aware chunking that never cuts through a word."""

import re

_SENTENCE_END = re.compile(r"(?<=[.!?;:])\s+")


def _pieces(paragraph: str, size: int) -> list[str]:
    """Split an oversized paragraph on sentences, then on words."""
    pieces: list[str] = []
    for sentence in _SENTENCE_END.split(paragraph):
        if len(sentence) <= size:
            pieces.append(sentence)
            continue
        line = ""
        for word in sentence.split():
            if line and len(line) + 1 + len(word) > size:
                pieces.append(line)
                line = ""
            line = f"{line} {word}".strip()
        if line:
            pieces.append(line)
    return pieces


def _tail(text: str, overlap: int) -> str:
    """Last words of a chunk, at most `overlap` characters, on a word boundary."""
    if overlap <= 0 or len(text) <= overlap:
        return ""
    tail = text[-overlap:]
    _, _, rest = tail.partition(" ")
    return rest.strip()


def chunk_text(text: str, size: int = 500, overlap: int = 80) -> list[str]:
    # 500 caractères ≈ 110 jetons, sous la limite de 128 du modèle d'embeddings.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    units: list[tuple[str, bool]] = []
    for paragraph in paragraphs:
        pieces = _pieces(paragraph, size) if len(paragraph) > size else [paragraph]
        for index, piece in enumerate(pieces):
            units.append((piece, index == 0))

    chunks: list[str] = []
    buffer = ""
    for piece, starts_paragraph in units:
        separator = "\n\n" if starts_paragraph else " "
        if not buffer:
            buffer = piece
        elif len(buffer) + len(separator) + len(piece) <= size:
            buffer = f"{buffer}{separator}{piece}"
        else:
            chunks.append(buffer)
            # Le chevauchement ne sert que pour un paragraphe coupé en deux.
            carry = "" if starts_paragraph else _tail(buffer, overlap)
            joined = f"{carry} {piece}".strip()
            buffer = joined if len(joined) <= size else piece
    if buffer:
        chunks.append(buffer)
    return chunks
