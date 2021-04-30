#!/bin/bash
set -e

mkdir -p data-tmp
cd data-tmp

GH_REPO_NAME="scaife-viewer/explorehomer-atlas"
GIT_REF="feature/atlas-yml"

curl -L "https://github.com/${GH_REPO_NAME}/archive/${GIT_REF}.tar.gz"  | tar zxf -
echo "Downloaded contents of ${GH_REPO_NAME} at ${GIT_REF}"
