FROM python:3.10
ENV PYTHONUNBUFFERED=1
COPY requirements.txt /project/requirements.txt
RUN pip install -r /project/requirements.txt

COPY src /project/src
RUN rm -rf /project/src/.env
COPY .docker.env /project/.env


WORKDIR /project/
