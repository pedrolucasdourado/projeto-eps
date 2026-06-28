FROM python:3.12-slim

WORKDIR /app

ENV HOME=/tmp

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libpq5 \
    libreoffice-writer \
    fonts-dejavu-core \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY templates ./templates

RUN groupadd --system aai && useradd --system --gid aai --home /app aai \
    && chown -R aai:aai /app

USER aai

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=3s --retries=8 --start-period=25s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
