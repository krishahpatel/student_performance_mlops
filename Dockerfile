FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /app

COPY app/requirements.txt /app/app/requirements.txt
RUN pip install --no-cache-dir --default-timeout=120 --retries=5 \
    -r /app/app/requirements.txt

COPY app /app/app
COPY src /app/src
COPY models /app/models

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')"

CMD ["waitress-serve", "--listen=0.0.0.0:5000", "app.app:app"]
