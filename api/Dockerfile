FROM python:3.12-slim

ENV HF_HOME=/opt/hf \
    PYTHONUNBUFFERED=1

WORKDIR /srv

COPY requirements.txt .
# Torch CPU : l'image par défaut embarque CUDA et pèse plusieurs Go de plus.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Le modèle est téléchargé au build : aucun téléchargement au démarrage.
ARG EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
RUN python -c "from sentence_transformers import SentenceTransformer as S; S('${EMBEDDING_MODEL}')"

COPY app ./app
COPY data ./data
COPY eval ./eval

RUN useradd --create-home --uid 10001 rag && chown -R rag /opt/hf
USER rag

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
