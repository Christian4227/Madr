FROM python:3.13-slim
WORKDIR /api

COPY . .
RUN python3 -m pip install uv
RUN uv pip install --system .

EXPOSE 8000
CMD ["uvicorn", "--host", "0.0.0.0", "madr.app:app"]