FROM python:3.13-slim
WORKDIR /api

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


COPY . .
RUN python3 -m pip install uv
RUN uv pip install --system .

EXPOSE 8000
CMD ["uvicorn", "--host", "0.0.0.0", "madr.app:app"]