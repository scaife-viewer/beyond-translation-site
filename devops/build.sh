#!/usr/bin/env bash
set -eu

GIT_REF=${1:-HEAD}
echo Exporting repository as of $GIT_REF
git archive $GIT_REF > ${TAG_NAME}.tgz
mkdir -p ${TAG_NAME}
tar -xvf ${TAG_NAME}.tgz -C ${TAG_NAME}
cd ${TAG_NAME}

echo Building deployment image
gcloud --project=scaife-viewer builds submit \
    --substitutions=TAG_NAME=${TAG_NAME}

echo Cleaning up
cd ..
rm -Rf ${TAG_NAME}.tgz ${TAG_NAME}

echo Done
