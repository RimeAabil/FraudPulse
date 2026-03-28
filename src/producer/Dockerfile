FROM python:3.11-slim

RUN groupadd -r producergroup && useradd -r -g producergroup produceruser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY producer.py .

USER produceruser

CMD ["python", "producer.py"]
