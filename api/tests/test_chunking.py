from app.chunking import chunk_text


def test_short_paragraphs_are_grouped():
    assert chunk_text("Un.\n\nDeux.\n\nTrois.", size=100) == ["Un.\n\nDeux.\n\nTrois."]


def test_chunks_respect_the_size_limit():
    text = "\n\n".join(f"Paragraphe numéro {i}. " * 20 for i in range(10))
    assert all(len(chunk) <= 500 for chunk in chunk_text(text))


def test_a_long_paragraph_never_cuts_a_word():
    words = [f"mot{i}" for i in range(400)]
    chunks = chunk_text(" ".join(words), size=120, overlap=30)
    assert len(chunks) > 1
    assert all(word in words for chunk in chunks for word in chunk.split())
    assert set(words) == {word for chunk in chunks for word in chunk.split()}


def test_a_cut_paragraph_overlaps_with_the_next_chunk():
    sentences = " ".join(f"Phrase numéro {i} du manuel." for i in range(60))
    first, second, *_ = chunk_text(sentences, size=200, overlap=60)
    assert first.split()[-1] in second.split()[:12]


def test_empty_text_gives_no_chunk():
    assert chunk_text("  \n\n  ") == []
