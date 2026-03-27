FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y swig libssl-dev dpkg-dev netcat-openbsd imagemagick libopencv-dev

COPY --from=ghcr.io/astral-sh/uv:0.7.2 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1
ADD uv.lock /code/
ADD pyproject.toml /code/
WORKDIR /code
RUN uv sync --frozen --no-dev --no-editable
ENV PATH="/code/.venv/bin:$PATH"

ADD misc/dokku/CHECKS /app/
ADD misc/dokku/* /code/

COPY . /code/
RUN /code/manage.py collectstatic --noinput
