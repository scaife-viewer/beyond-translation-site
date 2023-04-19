# # # # # # # # # # # # # # # # # # # # # # # #
# frontend
# # # # # # # # # # # # # # # # # # # # # # # #
FROM node:12.19.0-alpine AS frontend-build

RUN yarn global add @vue/cli@4.4.4

WORKDIR /app
COPY ./frontend/package.json ./frontend/yarn.lock ./
RUN yarn install

COPY ./frontend .
ENV VUE_APP_ABOUT_URL="https://sites.tufts.edu/perseusupdates/2023/03/15/perseus-6-0-beyond-translation-the-first-version-of-a-next-generation-perseus/"
RUN yarn build

# # # # # # # # # # # # # # # # # # # # # # # #
# backend
# # # # # # # # # # # # # # # # # # # # # # # #
FROM python:3.9 AS backend-build
WORKDIR /opt/scaife-stack/src/
RUN pip install --disable-pip-version-check --upgrade pip setuptools wheel virtualenv
ENV PATH="/opt/scaife-stack/bin:${PATH}" VIRTUAL_ENV="/opt/scaife-stack"
COPY ./backend/requirements.txt /opt/scaife-stack/src/
RUN set -x \
    && virtualenv /opt/scaife-stack \
    && pip install -r requirements.txt

# # # # # # # # # # # # # # # # # # # # # # # #
# backend data and code prep
# # # # # # # # # # # # # # # # # # # # # # # #
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
ARG ATLAS_DB_URL

RUN sh scripts/prepare-atlas-data.sh ${ATLAS_DB_URL}

RUN python manage.py loaddata fixtures/sites.json

# TODO: Revisit this if we tweak this multistage file
# to handle code / data changes out of band
# TODO: tocs not there; what to do?
RUN rm -Rf data
# TODO: Ensure $HEROKU_APP_NAME is applied via
# an entrypoint script
# RUN python manage.py update_site_for_review_app

# # # # # # # # # # # # # # # # # # # # # # # #
# webapp
# # # # # # # # # # # # # # # # # # # # # # # #
FROM backend-build as webapp
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
COPY ./backend/data/tocs /opt/scaife-stack/src/data/tocs

RUN python manage.py collectstatic

CMD gunicorn scaife_stack_atlas.wsgi
