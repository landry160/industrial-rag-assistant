import pytest
from fpdf import FPDF

from app.parsing import UnsupportedDocument, parse_document


def make_pdf(pages: list[str]) -> bytes:
    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)
    for text in pages:
        pdf.add_page()
        if text:
            pdf.multi_cell(0, 8, text)
    return bytes(pdf.output())


def test_pdf_keeps_page_numbers():
    sections = parse_document("manuel.pdf", make_pdf(["Page une", "", "Page trois"]))
    assert [s.page for s in sections] == [1, 3]
    assert "Page trois" in sections[1].text


def test_scanned_pdf_is_refused_with_a_clear_message():
    with pytest.raises(UnsupportedDocument, match="OCR"):
        parse_document("scan.pdf", make_pdf(["", ""]))


def test_damaged_pdf_is_refused():
    with pytest.raises(UnsupportedDocument):
        parse_document("casse.pdf", b"ceci n'est pas un pdf")


def test_text_handles_windows_encoding():
    sections = parse_document("note.txt", "Procédure d'arrêt".encode("cp1252"))
    assert sections[0].text == "Procédure d'arrêt"


@pytest.mark.parametrize("name", ["virus.exe", "tableau.xlsx", "sans_extension"])
def test_unknown_formats_are_refused(name):
    with pytest.raises(UnsupportedDocument, match="Format"):
        parse_document(name, b"data")


def test_empty_file_is_refused():
    with pytest.raises(UnsupportedDocument, match="vide"):
        parse_document("vide.txt", b"")
