import sys
from app.db import get_db_connection
from app.embeddings import embed

def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "quelle est la fréquence d'inspection du convoyeur ?"
    qv = embed([q])[0]
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            qv_str = "[" + ",".join(str(x) for x in qv) + "]"
            cur.execute(
                "SELECT source, content, embedding <=> %s::vector AS dist FROM chunks ORDER BY dist LIMIT 3",
                (qv_str,),
            )

            for src, content, dist in cur.fetchall():
                print(f"[{dist:.3f}] {src}\n  {content[:140]}...\n")

if __name__ == "__main__":
    main()
