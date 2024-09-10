FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY . .

RUN apk add --update --no-cache --virtual .tmp-build-deps \
        gcc libc-dev linux-headers postgresql-dev && \
    pip install --upgrade pip && \
    pip install wheel && \
    pip install --no-cache-dir -r requirements.txt

CMD ["sh", "-c", "python3 -m alembic upgrade head; python3 main.py"]