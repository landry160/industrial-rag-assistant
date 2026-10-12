
"""Answer generation grounded on retrieved passages."""

import os

from google import genai

MODEL = "gemini-3.8-flash"


def generate_answer(
    question: str,
    passages: list[tuple[str, str]],
) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("La variable GEMINI_API_KEY est absente.")

    context = "\n\n".join(
        f"[{src}] {text}" for src, text in passages
    )

    prompt = (
        "Tu es un assistant technique pour la maintenance industrielle. "
        "Réponds en français, UNIQUEMENT à partir des passages fournis. "
        "Si les passages ne contiennent pas la réponse, dis-le clairement.\n\n"
        f"Passages :\n{context}\n\n"
        f"Question : {question}\n\n"
        "Réponse :"
    )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )

    answer = response.text

    if not answer:
        raise RuntimeError(
            "Gemini n'a retourné aucun texte exploitable."
        )

    return answer.strip()
