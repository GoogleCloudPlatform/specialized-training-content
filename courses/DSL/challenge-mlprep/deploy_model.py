'''Usage: python3 deploy_model.py --model_dir $MODEL_DIR --model_name $MODEL_NAME

    Note: You need to have set a default region for Google Compute Engine and Vertex AI, you can do so with the follow commands:
    gcloud config set project $PROJECT
    gcloud config set ai/region $REGION
'''

import argparse
from google.cloud import aiplatform

if __name__=='__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_dir",
        help="Model location in GCS",
        type=str
    )
    parser.add_argument(
        "--model_name",
        help="Model name",
        type=str
    )
    
    args = parser.parse_args().__dict__

    model = aiplatform.Model.upload(
        display_name=args['model_name'],
        artifact_uri=args['model_dir'],
        serving_container_image_uri="us-docker.pkg.dev/cloud-aiplatform/prediction/tf2-cpu.2-12:latest",
    )

    endpoint = model.deploy(
        machine_type="n1-standard-2",
        min_replica_count=1,
        max_replica_count=1,
        accelerator_type=None,
        accelerator_count=None,
    )
