#!/bin/bash
set -e

if [ $1 ]
then
    echo "Downloading database"
    curl $1 > db.tgz
    tar -zxvf db.tgz
    mkdir -p ${DB_DATA_PATH}
    mv db.sqlite ${DATA_DIR}/db.sqlite
    rm db.tgz
else
    echo "[Running migrations and populating the ATLAS database]"
    # TODO: Ensure DB_DATA_PATH exists in `scaife-viewer-atlas`
    # command
    # TODO: Support loading data from a tarball upstream too
    mkdir -p $DB_DATA_PATH
    python manage.py prepare_atlas_db --force
fi
