import argparse
from google.cloud import aiplatform

if __name__=='__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--model_dir",
                        help="GCS model location",
                        type=str)

    args = (parser.parse_args()).__dict__


    ARTIFACT = args['model_dir']
    MODEL_NAME = "fraud_detection"

    SERVING_CONTAINER = (
        "us-docker.pkg.dev/cloud-aiplatform/prediction/tf2-cpu.2-12:latest"
    )

    model = aiplatform.Model.upload(
        display_name=MODEL_NAME,
        artifact_uri=ARTIFACT,
        serving_container_image_uri=SERVING_CONTAINER,
    )

    endpoint = model.deploy(
        machine_type="n1-standard-4",
        min_replica_count=1,
        max_replica_count=2,
        accelerator_type=None,
        accelerator_count=None,
    )

    print(f'Endpoint ID: {endpoint.resource_name}')