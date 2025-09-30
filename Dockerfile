# ========== Builder ==========
FROM python:3.12-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry>=2,<3"

WORKDIR /app
COPY pyproject.toml ./

RUN poetry install --no-root --only main --no-interaction --no-ansi

RUN cp -a "$(poetry env info -p)" /opt/venv

# ========== Runtime ==========
FROM python:3.12-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Non-root user
RUN useradd -m appuser
WORKDIR /app

# Bring in the ready-made virtualenv and your app code
COPY --from=builder /opt/venv /opt/venv
COPY flask_books_xss ./flask_books_xss

# SQLite storage
RUN mkdir -p /app/instance && chown -R appuser:appuser /app
VOLUME ["/app/instance"]

# Defaults (override at run)
ENV FLASK_APP=flask_books_xss.app \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000 \
    DATABASE_URL=sqlite:///instance/app.db \
    VULNERABLE_MODE=true

EXPOSE 5000
USER appuser
CMD ["python", "-m", "flask", "run"]
