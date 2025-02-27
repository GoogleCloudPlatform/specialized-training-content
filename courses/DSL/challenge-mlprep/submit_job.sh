#!/bin/bash 

# Usage: bash submit_job.sh $DATA_BUCKET \
#                           $ARTIFACT_REGISTRY \
#                           $IMAGE_NAME \
#                           $NUM_EXAMPLES \
#                           $NUM_BINS \
#                           $HASH_BKTS

# Output directory and jobID
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
OUTDIR=gs://${DATA_BUCKET}/fraud_detection/trained_model_$TIMESTAMP
JOB_NAME=fraud_detection_$TIMESTAMP
echo ${OUTDIR} ${REGION} ${JOB_NAME}

# Model and training hyperparameters
BATCH_SIZE=50
NUM_EXAMPLES_TO_TRAIN_ON=$4
NUM_EVALS=5
NUM_BINS=$5
HASH_BKTS=$6

# Vertex AI machines to use for training
MACHINE_TYPE=n1-standard-8
REPLICA_COUNT=1

# GCS paths.
GCS_PROJECT_PATH=gs://$1/fraud_detection
DATA_PATH=$GCS_PROJECT_PATH/data
TRAIN_DATA_PATH=$DATA_PATH/train*
EVAL_DATA_PATH=$DATA_PATH/eval*

ARTIFACT_REGISTRY_DIR=$2
IMAGE_NAME=$3
IMAGE_URI=us-docker.pkg.dev/$PROJECT/$ARTIFACT_REGISTRY_DIR/$IMAGE_NAME:latest

WORKER_POOL_SPEC="machine-type=$MACHINE_TYPE,\
replica-count=$REPLICA_COUNT,\
container-image-uri=$IMAGE_URI"

ARGS="--eval_data_path=$EVAL_DATA_PATH,\
--output_dir=$OUTDIR,\
--train_data_path=$TRAIN_DATA_PATH,\
--batch_size=$BATCH_SIZE,\
--num_examples_to_train_on=$NUM_EXAMPLES_TO_TRAIN_ON,\
--num_evals=$NUM_EVALS,\
--num_bins=$NUM_BINS,\
--hash_bkts=$HASH_BKTS"

gcloud ai custom-jobs create \
  --region=$REGION \
  --display-name=$JOB_NAME \
  --worker-pool-spec=$WORKER_POOL_SPEC \
  --args="$ARGS"
