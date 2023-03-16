# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip3 install -r requirements.txt

COPY db_utilities.py /app/db_utilities.py
COPY select_script.py /app/select_script.py
COPY language_detection.py /app/language_detection.py
COPY topic_modeling_LDA.py /app/topic_modeling_LDA.py



CMD ["python3", "select_script.py"]