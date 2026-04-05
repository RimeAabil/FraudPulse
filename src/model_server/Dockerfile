FROM python:3.11-slim

RUN groupadd -r modelgroup && useradd -r -g modelgroup modeluser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER modeluser
EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
