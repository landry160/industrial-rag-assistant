"""Quick check: print the chunks retrieved for a question."""

import sys

from app.retrieval import search


def main() -> None:
    question = (
        sys.argv[1] if len(sys.argv) > 1 else "quelle est la fréquence d'inspection du convoyeur ?"
    )
    for hit in search(question):
        print(f"[{hit.score:.3f}] {hit.document}\n  {hit.content[:140]}...\n")


if __name__ == "__main__":
    main()
