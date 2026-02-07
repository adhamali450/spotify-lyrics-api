FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY api/ ./api/

EXPOSE 8080

ENV PYTHONPATH=/app/src

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "api.app:app"]
