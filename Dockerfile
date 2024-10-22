FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONPATH=/project-cva

WORKDIR /project-cva

RUN apt-get update && apt-get install -y \
    python3-dev \
    build-essential \
    gcc \
    musl-dev

RUN pip install --upgrade pip
RUN pip install poetry

ADD pyproject.toml /project-cva

RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-interaction --no-ansi

COPY . /project-cva
