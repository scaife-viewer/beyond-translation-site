#!/usr/bin/env bash
set -eu

REVISION=$1
TAG=$2

echo adding $TAG to $REVISION...
gcloud run services update-traffic beyond-translation-dev-us-central1 \
    --project="scaife-viewer" \
    --region="us-central1" \
    --update-tags=${TAG}=${REVISION}
