#!/bin/bash
# Build the notes-app image for Cloud Run (linux/amd64) and push it to Artifact
# Registry. Cloud Run runs amd64, so we cross-build from Apple Silicon via
# buildx and push straight to the registry (a non-native arch can't be loaded
# into the local Docker store anyway).
#
# Override the target by exporting any of these before running:
#   AR_HOST     registry host       (default: us-docker.pkg.dev)
#   AR_PROJECT  registry project    (default: jwd-gcp-demos)   <- switch to qwiklabs-resources when granted
#   AR_REPO     repository name      (default: specialized-training)
#   IMAGE_NAME  image name           (default: notes-app)
#   IMAGE_TAG   tag                  (default: latest)
set -eo pipefail

AR_HOST="${AR_HOST:-us-docker.pkg.dev}"
AR_PROJECT="${AR_PROJECT:-jwd-gcp-demos}"
AR_REPO="${AR_REPO:-specialized-training}"
IMAGE_NAME="${IMAGE_NAME:-notes-app}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

IMAGE="${AR_HOST}/${AR_PROJECT}/${AR_REPO}/${IMAGE_NAME}:${IMAGE_TAG}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ensure Docker has a credential helper for this registry host (idempotent).
gcloud auth configure-docker "$AR_HOST" --quiet

echo ">>> Building linux/amd64 and pushing: $IMAGE"
docker buildx build --platform linux/amd64 -t "$IMAGE" --push "$SCRIPT_DIR"

echo ">>> Done. Pushed $IMAGE"
