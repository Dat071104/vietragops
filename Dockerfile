FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip \
    && pip install -r /app/requirements.txt \
    && useradd --create-home --uid 10001 appuser

COPY . /app

# The release context must carry the exact GCS corpus copy. This is a
# fail-closed image-build backstop; the host-side verification command must
# run before Cloud Build is invoked as documented in deploy/gcp/README.md.
RUN test -f /app/deploy/corpus-release/release.json \
    && python -B /app/scripts/verify_vector_artifact.py \
        --artifact-dir /app/data/chunks/embeddings/active \
        --release-dir /app/deploy/corpus-release \
        --model-id intfloat/multilingual-e5-small \
        --model-revision 614241f622f53c4eeff9890bdc4f31cfecc418b3

RUN mkdir -p /app/data/lifecycle /tmp/vietragops-cloud-cache \
    && chown -R appuser:appuser /app /tmp/vietragops-cloud-cache

USER appuser

EXPOSE 8000
EXPOSE 8501

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
