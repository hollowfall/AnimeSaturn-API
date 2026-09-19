FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt pyproject.toml ./
COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r server/requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT}"]
