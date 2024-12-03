FROM python:3.12

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y fonts-roboto

WORKDIR /app

# Requirements
RUN pip3 install poetry==1.8.3
COPY ./pyproject.toml /app
COPY ./poetry.lock /app
RUN poetry config virtualenvs.create false && \
    poetry install
