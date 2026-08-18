FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install "Werkzeug==2.0.3" "gunicorn==20.1.0"

COPY . /app

RUN chmod +x /app/docker-entrypoint.sh /app/docker-updater.sh \
    && mkdir -p /app/data

EXPOSE 5000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind=0.0.0.0:5000", "--workers=1", "--threads=4", "--timeout=120", "serve:app"]
