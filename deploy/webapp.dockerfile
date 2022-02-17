ARG FRONTEND_IMAGE=docker.io/beyond-translation/frontend-build:latest
ARG BACKEND_IMAGE=docker.io/beyond-translation/backend-build:latest
ARG BACKEND_PREP_IMAGE=docker.io/beyond-translation/backend-prep:latest

FROM ${FRONTEND_IMAGE} as frontend-build
FROM ${BACKEND_PREP_IMAGE} as backend-prep

FROM ${BACKEND_IMAGE}
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

RUN python manage.py collectstatic --noinput
