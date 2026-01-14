FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

# ========================
# deps
# ========================
FROM base AS deps

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock* README.md ./

RUN python -m pip install --no-cache-dir uv \
 && uv pip install --system --no-cache .

# ========================
# runtime
# ========================
FROM base AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser

COPY --from=deps /usr/local /usr/local
COPY . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "madr.app:app", "--host", "0.0.0.0", "--port", "8000"]
