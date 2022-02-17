ARG BACKEND_IMAGE=docker.io/beyond-translation/backend-build:latest

FROM ${BACKEND_IMAGE}

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/opt/scaife-stack/src/ \
    PATH="/opt/scaife-stack/bin:${PATH}" \
    VIRTUAL_ENV="/opt/scaife-stack" \
    DB_DATA_PATH="/opt/scaife-stack/db-data"

WORKDIR /opt/scaife-stack/src/
COPY . .

ARG HEROKU_APP_NAME

RUN sh scripts/prepare-atlas-data.sh

RUN python manage.py loaddata fixtures/sites.json
# TODO: Ensure $HEROKU_APP_NAME is applied via
# an entrypoint script
# RUN python manage.py update_site_for_review_app
