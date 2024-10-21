"""Argument definitions for model training code in `trainer.model`."""

import argparse

from trainer import model

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--batch_size",
        help="Batch size for training steps",
        type=int,
        default=32,
    )
    parser.add_argument(
        "--eval_data_path",
        help="GCS location pattern of eval files",
        required=True,
    )
    
    parser.add_argument(
        "--num_bins",
        help="Number of buckets for float-valued fields",
        type=int,
        default=10,
    )
    
    parser.add_argument(
        "--hash_bkts",
        help="Number of hash buckets for id fields",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--num_evals",
        help="Number of times to evaluate model on eval data training.",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--num_examples_to_train_on",
        help="Number of examples to train on.",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--output_dir",
        help="GCS location to write checkpoints and export models",
        required=True,
    )
    parser.add_argument(
        "--train_data_path",
        help="GCS location pattern of train files containing eval URLs",
        required=True,
    )
    args = parser.parse_args()
    hparams = args.__dict__

    model.train_and_evaluate(hparams)
