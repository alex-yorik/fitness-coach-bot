FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -r -s /bin/false -u 10001 appuser \
    && mkdir -p /app/data /app/media /app/logs /app/scripts \
    && chown -R appuser:appuser /app/data /app/media /app/logs \
    && chmod 755 /app /app/admin /app/app /app/scripts

USER appuser

CMD ["python", "app/bot.py"]
