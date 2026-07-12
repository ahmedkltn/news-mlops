FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Big ML wheels; slow mirrors time out on the default 15s. Give pip room.
ENV PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=8
# CPU-only torch first (no GPU in container) — avoids the ~2.5GB CUDA wheel
# stack. requirements.txt's unpinned `torch` is then already satisfied.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
