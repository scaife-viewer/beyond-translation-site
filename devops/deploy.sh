#!/usr/bin/env bash
set -eu

gcloud run deploy beyond-translation-dev-us-central1 \
    --project="scaife-viewer" \
    --region="us-central1" \
    --image gcr.io/scaife-viewer/beyond-translation-site:"${TAG_NAME}" \
    --allow-unauthenticated \
    --no-traffic \
    --tag="git-${TAG_NAME}"
