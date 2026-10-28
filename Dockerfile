FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir flask==3.1.3 gunicorn==23.0.0 \
    && useradd --create-home --uid 1000 gunsystem \
    && chown gunsystem /app

COPY --chown=gunsystem gunsystem ./gunsystem
COPY --chown=gunsystem demo ./demo
COPY --chown=gunsystem webapp ./webapp

USER gunsystem
EXPOSE 8000

# One worker only: the last balance run and the session signing key live in process memory.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "120", "webapp:create_app()"]
