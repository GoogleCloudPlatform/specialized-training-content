#!/usr/bin/env bash
cd ~

function setup_logger() {
  exec 1> >(stdbuf -i0 -oL -eL sed -e 's/^/'"$1: "'/') 2>&1
}

setup_logger "delete-apigeex-org"

echo "*** Setting env variables ***"
export PROJECT_ID=$(gcloud config get-value project)

echo "*** Updating apt package list ***"
apt-get update

# Delete the Apigee Eval Org
gcloud alpha apigee organizations delete $PROJECT_ID
