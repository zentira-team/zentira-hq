FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN useradd -m -u 1000 user
WORKDIR /app

COPY --chown=user:user requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY --chown=user:user . /app
RUN mkdir -p /app/data /app/outputs && chown -R user:user /app/data /app/outputs

USER user
EXPOSE 8000

CMD ["sh", "-c", "python main.py office --host 0.0.0.0 --port ${PORT:-8000} --no-browser"]
