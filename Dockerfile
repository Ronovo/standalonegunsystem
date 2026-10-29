FROM python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_URL=https://github.com/Ronovo/standalonegunsystem.git \
    BUILD_CMD="pip install --no-cache-dir --user -q .[web]" \
    DATA_DIR=/app/data

WORKDIR /app

COPY docker/git-sync.sh /usr/local/bin/git-sync
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && chmod +x /usr/local/bin/git-sync

COPY pyproject.toml README.md ./
COPY gunsystem ./gunsystem
RUN pip install --no-cache-dir ".[web]" gunicorn==23.0.0 \
    && useradd --create-home --uid 1000 gunsystem \
    && mkdir -p /app/data \
    && chown -R gunsystem /app

COPY --chown=gunsystem demo ./demo
COPY --chown=gunsystem webapp ./webapp

USER gunsystem
EXPOSE 8000

# One worker only: the last balance run and the session signing key live in process memory.
ENTRYPOINT ["git-sync"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "120", "webapp:create_app()"]
