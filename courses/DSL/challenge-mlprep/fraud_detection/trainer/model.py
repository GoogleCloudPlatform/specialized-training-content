"""
This Python script is used for preparing model features, training the machine learning model, and 
exporting the trained model for prediction purposes. The train_and_evaluate function is called 
by trainer.task after parsing input arguments.
"""

from functools import partial
import logging
import os

import numpy as np
import tensorflow as tf
from tensorflow.keras import callbacks
from tensorflow.keras.layers import (
    Concatenate,
    Dense,
    Hashing,
    Discretization,
    CategoryEncoding,
    IntegerLookup,
    StringLookup,
    Flatten,
    Input,
    Lambda,
)

logging.info(tf.version.VERSION)

# Define headers for CSV input and split into different lists for 
# integer, float and categorical features

CSV_COLS = ['step',
            'action',
            'amount',
            'idOrig',
            'oldBalanceOrig',
            'newBalanceOrig',
            'idDest',
            'oldBalanceDest',
            'newBalanceDest',
            'isFraud']
INT_COLS = ['step']
FLOAT_COLS = ['oldBalanceOrig', 'newBalanceOrig', 'amount',
            'oldBalanceDest', 'newBalanceDest']
CAT_COLS = ['action', 'idOrig', 'idDest']

# Specify name of column containing labels and set default values for columns. 
# Note that the order of the defaults is the same as the order of the columns in the CSV.

LABEL_COLUMN = "isFraud"
DEFAULTS = [[0],["na"],[0.0],["na"],[0.0],[0.0],["na"],[0.0],[0.0],[0]]

INPUT_COLS = [
    c for c in CSV_COLS if c != LABEL_COLUMN
]

# Function to separate an instance into a dictionary of features and a label.
def features_and_labels(row_data):
    label = row_data.pop(LABEL_COLUMN)
    return row_data, label

# Function to load CSV files into a TF Dataset object. Note that these are not stored in memory and
# portions of the file are loaded as needed. This is all managed by the tf.data.Dataset object and 
# methods.
def load_dataset(pattern, batch_size, num_repeat):
    dataset = tf.data.experimental.make_csv_dataset(
        file_pattern=pattern,
        batch_size=batch_size,
        column_names=CSV_COLS,
        column_defaults=DEFAULTS,
        num_epochs=num_repeat,
        shuffle_buffer_size=10000,
        header=True
    )
    return dataset.map(features_and_labels)

# Helper function to create the training tf.data.Dataset object
def create_train_dataset(pattern, batch_size):
    dataset = load_dataset(pattern, batch_size, num_repeat=None)
    return dataset.prefetch(1)


# Helper function to create the tf.data.Dataset object for adapting preprocessing layers
def create_adapt_dataset(pattern, batch_size):
    dataset = load_dataset(pattern, batch_size, num_repeat=1)
    return dataset.prefetch(1)

# Helper function to create the evaluation tf.data.Dataset object
def create_eval_dataset(pattern, batch_size):
    dataset = load_dataset(pattern, batch_size, num_repeat=1)
    return dataset.prefetch(1)

# Helper function to create Keras input and creata + adapt preprocessing layers.
# Returns list of Input layers and dictionary of input features (layers) for the neural network. 
def get_input_and_transform(ds, num_bins, hash_bkts):
    
    inputs = {}
    
    # Create Input layers with appropriate datatype for each column
    for col in INT_COLS:
        inputs[col] = Input(name=col, shape=(1,), dtype=tf.int32)
    for col in CAT_COLS:
        inputs[col] = Input(name=col, shape=(1,), dtype=tf.string)
    for col in FLOAT_COLS:
        inputs[col] = Input(name=col, shape=(1,), dtype=tf.float32)
    
    feature_ds = ds.map(lambda x, y: x)
    
    # Helper function to get column from dataset
    def _get_col(ds,col):
        return ds[col] 
    
    transformed = {}

    # One-hot encode integer valued columns
    layer = IntegerLookup(output_mode='one_hot')
    logging.warn("Adapting 'step' IntegerLookup layer.")
    layer.adapt(feature_ds.map(partial(_get_col, col='step')), steps=100)
    transformed['step'] = layer(inputs['step'])

    # One-hot encode categorical columns
    layer = StringLookup(output_mode='one_hot')
    logging.warn("Adapting 'action' StringLookup layer.")
    layer.adapt(feature_ds.map(partial(_get_col, col='action')), steps=100)
    transformed['action'] = layer(inputs['action'])

    # Bucketize float-valued columns into num_bins buckets
    for col in FLOAT_COLS:
        layer = Discretization(num_bins=num_bins, output_mode='one_hot')
        logging.warn(f"Adapting {col} Discretization layer.")
        layer.adapt(feature_ds.map(partial(_get_col, col=col)), steps=100)
        # layer = CategoryEncoding(num_bins, output_mode='one_hot')
        transformed[col] = layer(inputs[col])

    # Use hash buckets for idOrig and idDest features to minimize sparsity
    for col in ['idOrig', 'idDest']:
        layer = Hashing(hash_bkts, output_mode='one_hot')
        transformed[col] = layer(inputs[col])
                                
    return inputs, transformed
                                 
# Function to build the neural network to be trained. 
def build_dnn_model(ds, num_bins, hash_bkts):
    
    inputs, transformed = get_input_and_transform(ds, num_bins, hash_bkts)
    
    # Concatenate preprocessed features into a single layer of the right dimension
    dnn_inputs = Concatenate()(transformed.values())
    dnn_inputs = Flatten()(dnn_inputs)

    # Create a DNN with 3 layers and ReLU activation. Output is predicted probability that a 
    # transaction is fraudulent.
    hid_1 = tf.keras.layers.Dense(64, activation='relu')(dnn_inputs)
    hid_2 = tf.keras.layers.Dense(32, activation='relu')(hid_1)
    hid_3 = tf.keras.layers.Dense(16, activation='relu')(hid_2)
    logit = tf.keras.layers.Dense(1, activation='sigmoid')(hid_3)  

    # List of metrics to be computed at training and evaluation time. 
    metrics = [tf.keras.metrics.BinaryAccuracy(),
               tf.keras.metrics.Precision(),
               tf.keras.metrics.Recall(),
               tf.keras.metrics.AUC(curve='PR')]

    # Create and compile the model with BinaryCrossentropy loss function
    model = tf.keras.Model(inputs=inputs, outputs=logit)
    model.compile(loss=tf.keras.losses.BinaryCrossentropy(from_logits=False), metrics=metrics)

    return model

# Function to train and evaluate the neural network model. This function is called in trainer.task
def train_and_evaluate(hparams):

    # Parse parameters for train and evaluate process. Includes:
    # num_bins: Number of buckets for float-valued columns
    # hash_bkts: Number of hash buckets for idOrig and idDest features
    # batch_size: Batch size for training loop
    # train_data_path: Location of training data CSVs
    # eval_data_path: Location of eval data CSVs
    # num_evals: Number of evaluations to perform during training process
    # num_examples_to_train_on: Total number of examples to train on
    # output_dir: Output directory for model artifacts post-training

    num_bins = hparams["num_bins"]
    hash_bkts = hparams["hash_bkts"]
    batch_size = hparams["batch_size"]
    train_data_path = hparams["train_data_path"]
    eval_data_path = hparams["eval_data_path"]
    num_evals = hparams["num_evals"]
    num_examples_to_train_on = hparams["num_examples_to_train_on"]
    output_dir = hparams["output_dir"]

    # Define output paths for model artifacts and create directory if needed

    model_export_path = os.path.join(output_dir, "savedmodel")
    checkpoint_path = os.path.join(output_dir, "checkpoints")
    tensorboard_path = os.path.join(output_dir, "tensorboard")

    if tf.io.gfile.exists(output_dir):
        tf.io.gfile.rmtree(output_dir)
        
    # Create training, adaptation and evaluation datasets using helper functions

    trainds = create_train_dataset(train_data_path, batch_size)
    adaptds = create_adapt_dataset(train_data_path, batch_size)
    evalds = create_eval_dataset(eval_data_path, batch_size)
    
    # Build DNN model and print summary to logs using helper function

    model = build_dnn_model(adaptds, num_bins, hash_bkts)
    logging.info(model.summary())

    # Define number of training steps per evaluation during training process
    steps_per_epoch = num_examples_to_train_on // (batch_size * num_evals)

    # Define callbacks to save model checkpoints (per eval) and log metrics for Tensorboard
    checkpoint_cb = callbacks.ModelCheckpoint(
        checkpoint_path, save_weights_only=True, verbose=1
    )
    tensorboard_cb = callbacks.TensorBoard(tensorboard_path, histogram_freq=0)

    # Train Keras model and store evaluation metrics in dictionary called history
    history = model.fit(
        trainds,
        validation_data=evalds,
        epochs=num_evals,
        steps_per_epoch=max(1, steps_per_epoch),
        verbose=1,  # 0=silent, 1=progress bar, 2=one line per epoch
        callbacks=[checkpoint_cb, tensorboard_cb],
    )

    # Exporting the model with default serving function.
    model.save(model_export_path)
    return history
