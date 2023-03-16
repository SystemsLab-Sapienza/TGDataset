# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements_create_db.txt /app/requirements_create_db.txt

RUN pip3 install -r requirements_create_db.txt

COPY db_utilities.py /app/db_utilities.py


CMD ["python3", "db_utilities.py"]