# The coverage reports only show what the tests reach, so failing tests or low coverage still build the image.
FROM python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159 AS python-coverage
WORKDIR /src
COPY pyproject.toml README.md ./
COPY gunsystem ./gunsystem
RUN pip install --no-cache-dir ".[web,test]"
COPY . .
RUN python -m coverage run -m unittest discover -s tests -t . ; \
    python -m coverage html --fail-under=0 ; mkdir -p coverage/python ; \
    python -m coverage json --fail-under=0 -o coverage.json ; \
    python coverage-index/tools/functions.py coverage.json coverage/python/functions.json

FROM node:24-slim@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c AS js-coverage
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npx vitest run --coverage ; mkdir -p coverage/js ; cat coverage-index/istanbul.css >> coverage/js/base.css

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
COPY --chown=gunsystem coverage-index/index.html ./coverage/
COPY --chown=gunsystem coverage-reports.json ./coverage/reports.json
COPY --chown=gunsystem --from=python-coverage /src/coverage/python ./coverage/python
COPY --chown=gunsystem --from=js-coverage /src/coverage/js ./coverage/js

USER gunsystem
EXPOSE 8000

# One worker only: the last balance run and the session signing key live in process memory.
ENTRYPOINT ["git-sync"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "120", "webapp:create_app()"]
