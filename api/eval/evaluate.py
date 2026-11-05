"""Retrieval evaluation on the sample corpus.

Run in the API container, with the real embedding model:

    docker compose exec api python -m eval.evaluate

Prints Hit@1, Hit@k, MRR, then a threshold sweep to choose RETRIEVAL_MIN_SCORE:
the right value keeps every answerable question and rejects out-of-scope ones.
"""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from app import config
from app.db import init_db
from app.main import ingest_sample
from app.retrieval import Hit, search

GOLDEN = Path(__file__).with_name("golden.json")


@dataclass
class Report:
    hit_at_1: float
    hit_at_k: float
    mrr: float
    best_answerable: list[float]
    best_out_of_scope: list[float]


def _relevant(hit: Hit, case: dict) -> bool:
    return hit.document == case["document"] and case["contains"] in hit.content


def evaluate(k: int = config.TOP_K) -> Report:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    hits_1 = hits_k = 0
    reciprocal = 0.0
    best_answerable: list[float] = []

    for case in golden["answerable"]:
        hits = search(case["question"], k)
        rank = next((i for i, h in enumerate(hits, 1) if _relevant(h, case)), None)
        hits_1 += rank == 1
        hits_k += rank is not None
        reciprocal += 1 / rank if rank else 0.0
        best_answerable.append(max((h.score for h in hits), default=0.0))

    out_of_scope = [
        max((h.score for h in search(q, k)), default=0.0)
        for q in golden["out_of_scope"]
    ]
    total = len(golden["answerable"])
    return Report(hits_1 / total, hits_k / total, reciprocal / total, best_answerable, out_of_scope)


def sweep(report: Report) -> list[tuple[float, float, float]]:
    """(threshold, share of answerable kept, share of out-of-scope rejected)."""
    rows = []
    for tenths in range(1, 9):
        threshold = tenths / 10
        kept = sum(s >= threshold for s in report.best_answerable)
        rejected = sum(s < threshold for s in report.best_out_of_scope)
        rows.append(
            (
                threshold,
                kept / len(report.best_answerable),
                rejected / len(report.best_out_of_scope),
            )
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", type=int, default=config.TOP_K)
    args = parser.parse_args()

    init_db()
    ingest_sample()
    report = evaluate(args.k)

    if config.EMBEDDING_BACKEND == "hash":
        print("ATTENTION : backend de test, ces chiffres ne mesurent pas la qualité réelle.\n")
    print(f"Modèle : {config.EMBEDDING_ID}")
    print(f"Hit@1 : {report.hit_at_1:.0%}")
    print(f"Hit@{args.k} : {report.hit_at_k:.0%}")
    print(f"MRR : {report.mrr:.3f}\n")
    print("Seuil   Répondables gardées   Hors sujet rejetées")
    for threshold, kept, rejected in sweep(report):
        marker = " <- actuel" if abs(threshold - config.MIN_SCORE) < 0.001 else ""
        print(f"{threshold:.1f}     {kept:>19.0%}   {rejected:>19.0%}{marker}")


if __name__ == "__main__":
    main()
