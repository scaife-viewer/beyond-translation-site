#!/bin/bash
set -e

trap "exit" INT

APP_TAG_BASE="beyond-translation"

# TODO: Buildx?
# Build frontend
docker build -f deploy/frontend-build.dockerfile \
    --tag=${APP_TAG_BASE}/frontend-build \
    frontend

docker build -f deploy/backend-build.dockerfile \
    --tag=${APP_TAG_BASE}/backend-build \
    backend

docker build -f deploy/backend-prep.dockerfile \
    --tag=${APP_TAG_BASE}/backend-prep \
    --build-arg BACKEND_IMAGE=${APP_TAG_BASE}/backend-build \
    backend

docker build -f deploy/webapp.dockerfile \
    --tag=${APP_TAG_BASE}/webapp \
    --build-arg BACKEND_IMAGE=${APP_TAG_BASE}/backend-build \
    --build-arg FRONTEND_IMAGE=${APP_TAG_BASE}/frontend-build \
    --build-arg BACKEND_PREP_IMAGE=${APP_TAG_BASE}/backend-prep \
    backend
