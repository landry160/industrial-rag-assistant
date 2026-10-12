def chunk_text(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, buf = [], ""
    for p in paras:
        if len(buf) + len(p) + 2 <= size:
            buf = (buf + "\n\n" + p).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    out = []
    for c in chunks:
        if len(c) <= size:
            out.append(c)
        else:
            start = 0
            while start < len(c):
                out.append(c[start:start + size])
                start += size - overlap
    return out
 