FROM python:3.8-slim
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y swig libssl-dev dpkg-dev netcat-openbsd imagemagick libopencv-dev

RUN pip install -U --pre pip poetry==1.5.1
ADD poetry.lock /code/
ADD pyproject.toml /code/
RUN poetry config virtualenvs.create false
WORKDIR /code
RUN poetry install --no-dev --no-interaction --no-root

ADD misc/dokku/CHECKS /app/
ADD misc/dokku/* /code/

COPY . /code/
RUN /code/manage.py collectstatic --noinput
