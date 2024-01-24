#!/usr/bin/env bash
cd ~

function setup_logger() {
  exec 1> >(stdbuf -i0 -oL -eL sed -e 's/^/'"$1: "'/') 2>&1
}

setup_logger "delete-apigeex-org"

echo "*** Setting env variables ***"
export PROJECT_ID=$(gcloud config get-value project)
export TOKEN=$(gcloud auth print-identity-token)

echo "*** Updating apt package list ***"
apt-get update

# Delete the Apigee Eval Org with MINIMUM retention 
curl -X DELETE "https://apigee.googleapis.com/v1/organizations/$PROJECT_ID?retention=MINIMUM" -H "Authorization: Bearer $TOKEN"

gcloud alpha apigee organizations delete $PROJECT_ID
  

