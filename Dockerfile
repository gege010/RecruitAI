FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=production
WORKDIR /app
COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir -r requirements.txt -c requirements.lock \
    && useradd --create-home --uid 10001 recruitai \
    && mkdir -p /app/var && chown recruitai:recruitai /app/var
COPY --chown=recruitai:recruitai server/ ./server/
COPY --chown=recruitai:recruitai core/mcdm/ ./core/mcdm/
COPY --chown=recruitai:recruitai core/__init__.py ./core/__init__.py
COPY --chown=recruitai:recruitai web/ ./web/
USER recruitai
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
