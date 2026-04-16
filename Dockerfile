FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# pendings/ 掛載點 (由 docker-compose 或 -v 掛載到 toxicology-vault/pendings/)
VOLUME ["/vault/pendings"]

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
