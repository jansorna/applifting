FROM python:3.10.6-slim-buster

ENV PYTHONUNBUFFERED 1
RUN mkdir /applifting
WORKDIR /applifting
COPY . /applifting/
RUN pip install -r requirements.txt

