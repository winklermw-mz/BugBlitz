FROM python:3.12-slim

ENV LLM_HOST="http://host.docker.internal:8001/chat"
ENV LLM_API_KEY="lm-studio"
ENV LLM_MODEL="qwen/qwen3-vl-4b"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY model /app/model
COPY static /app/static
COPY templates /app/templates
COPY utils /app/utils
COPY route /app/route
COPY app.py /app/app.py

EXPOSE 8003

CMD ["python", "app.py"]