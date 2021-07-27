#!/bin/bash
set -e

echo "[Running migrations and populating the ATLAS database]"
# TODO: Fix in scaife-viewr-atlas
mkdir -p $DB_DATA_PATH
python manage.py prepare_atlas_db --force
