#!/usr/bin/env bash
set -eu

REVISION=$1
TAG=$2

echo adding $TAG to $REVISION...
gcloud run services update-traffic beyond-translation-site \
    --project="scaife-viewer" \
    --region="us-central1" \
    --update-tags=${TAG}=${REVISION}
