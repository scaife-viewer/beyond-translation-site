FROM node:12.19.0-alpine AS frontend-build

RUN yarn global add @vue/cli

WORKDIR /app
COPY ./frontend/package.json ./frontend/yarn.lock ./
RUN yarn install

COPY ./frontend .
RUN yarn build

FROM python:3.9 AS backend-build
WORKDIR /opt/scaife-stack/src/
RUN pip install --disable-pip-version-check --upgrade pip setuptools wheel virtualenv
ENV PATH="/opt/scaife-stack/bin:${PATH}" VIRTUAL_ENV="/opt/scaife-stack"
COPY ./backend/requirements.txt /opt/scaife-stack/src/
RUN set -x \
    && virtualenv /opt/scaife-stack \
    && pip install -r requirements.txt

FROM backend-build as backend-prep

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/opt/scaife-stack/src/ \
    PATH="/opt/scaife-stack/bin:${PATH}" \
    VIRTUAL_ENV="/opt/scaife-stack" \
    DB_DATA_PATH="/opt/scaife-stack/db-data"

WORKDIR /opt/scaife-stack/src/
COPY ./backend .

ARG HEROKU_APP_NAME

RUN sh scripts/prepare-atlas-data.sh

RUN python manage.py loaddata fixtures/sites.json
# TODO: Ensure $HEROKU_APP_NAME is applied via
# an entrypoint script
# RUN python manage.py update_site_for_review_app

FROM backend-build as atlas-slim
WORKDIR /opt/scaife-stack/src/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/opt/scaife-stack/src/ \
    PATH="/opt/scaife-stack/bin:${PATH}" \
    VIRTUAL_ENV="/opt/scaife-stack" \
    DB_DATA_PATH="/opt/scaife-stack/db-data" \
    PORT=8000

COPY --from=frontend-build /app/dist /opt/scaife-stack/src/static
# TODO: we may be able to tweak this COPY directive slightly
COPY --from=backend-prep /opt/scaife-stack /opt/scaife-stack

RUN python manage.py collectstatic
