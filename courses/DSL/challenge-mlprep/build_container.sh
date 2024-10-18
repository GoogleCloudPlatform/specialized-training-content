#!/bin/bash 

PROJECT_DIR=$(cd ./fraud_detection && pwd) #Should point towards the fraud_detection folder with Dockerfile
ARTIFACT_REGISTRY_DIR=dsl-artifact-repo
IMAGE_NAME=fraud_detection_training_container
DOCKERFILE=$PROJECT_DIR/Dockerfile
IMAGE_URI=us-docker.pkg.dev/$PROJECT/$ARTIFACT_REGISTRY_DIR/$IMAGE_NAME

gcloud artifacts repositories create dsl-artifact-repo \
    --repository-format=docker \
    --location=us \
    --description="Artifact repository for DSL" \
    --immutable-tags \
    --async

# Authorize docker command for Artifact Registry
gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin https://us-docker.pkg.dev

docker build $PROJECT_DIR -f $DOCKERFILE -t $IMAGE_URI

docker push $IMAGE_URI