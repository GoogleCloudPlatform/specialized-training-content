"""Data prep, train and evaluate DNN model."""

import logging
import os

import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import (
    Concatenate,
    Dense,
    Hashing,
    Discretization,
    IntegerLookup,
    StringLookup,
    Embedding,
    Flatten,
    Input,
    Lambda,
)
from tensorflow.keras.layers.experimental.preprocessing import HashedCrossing

logging.info(tf.version.VERSION)

INT_COLS = ['step']
FLOAT_COLS = ['oldBalanceOrig', 'newBalanceOrig', 'amount',
            'oldBalanceDest', 'newBalanceDest']
CAT_COLS = ['action', 'idOrig', 'idDest']
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

LABEL_COLUMN = "isFraud"
# DEFAULTS = 

INPUT_COLS = [
    c for c in CSV_COLUMNS if c != LABEL_COLUMN
]

def features_and_labels(row_data):
    label = tf.cast(row_data.pop(LABEL_COLUMN), tf.int64)
    return row_data, label

def load_dataset(pattern, batch_size, num_repeat):
    dataset = tf.data.experimental.make_csv_dataset(
        file_pattern=pattern,
        batch_size=batch_size,
        column_names=CSV_COLUMNS,
        num_epochs=num_repeat,
        shuffle_buffer_size=1000000,
    )
    return dataset.map(features_and_labels)


def create_train_dataset(pattern, batch_size):
    dataset = load_dataset(pattern, batch_size, num_repeat=None)
    return dataset.prefetch(1)


def create_eval_dataset(pattern, batch_size):
    dataset = load_dataset(pattern, batch_size, num_repeat=1)
    return dataset.prefetch(1)

def get_input_and_transform(num_bins, hash_bkts):
    
    inputs = {}
    transformed = {}
    
    for col in INT_COLS:
        inputs[col] = Input(name=col, shape=(1,), dtype='int64')
    for col in CAT_COLS:
        inputs[col] = Input(name=col, shape=(1,), dtype='string')
    for col in FLOAT_COLS:
        inputs[col] = Input(name=col, shape=(1,), dtype='float64')

    layer = IntegerLookup(output_mode='one_hot')
    layer.adapt(inputs['step'])
    transformed['step'] = layer(inputs['step']
    
    for col in FLOAT_COLS:
        layer = Discretization(num_bins=num_bins)
        layer.adapt(inputs[col])
        layer = CategoryEncoding(num_bins, output_mode='one_hot')
        transformed[col] = layer(inputs[col])
                                
    layer = StringLookup(output_mode='one_hot')
    layer.adapt(inputs['step'])
    transformed['step'] = layer(inputs['step']
                                
    for col in ['idOrig', 'idDest']:
        layer = Hashing(hash_bkts, output_mode='one_hot')
        transformed[col] = layer(inputs[col])
                                
    return inputs, transformed
                                 

def build_dnn_model(num_bins, hash_bkts):
    
    # transforms
    inputs, transformed = get_input_and_transform(num_bins, hash_bkts)
    dnn_inputs = Concatenate()(transformed.values())
    hid_1 = tf.keras.layers.Dense(64, activation='relu')(dnn_inputs)
    hid_2 = tf.keras.layers.Dense(32, activation='relu')(hid_1)
    hid_3 = tf.keras.layers.Dense(16, activation='relu')(hid_2)
    output = tf.keras.layers.Dense(1, activation='sigmoid')(hid_3)

    metrics = [tf.keras.metrics.BinaryAccuracy(),
               tf.keras.metrics.Precision(),
               tf.keras.metrics.Recall(),
               tf.keras.metrics.AUC(curve='PR')]

    model = tf.keras.Model(inputs=inputs, outputs=output)
    model.compile(loss=tf.keras.losses.BinaryFocalCrossentropy(apply_class_balancing=True), metrics=metrics)

    return model


def train_and_evaluate(hparams):
    # TODO 1b
    num_bins = hparams["num_bins"]
    hash_bkts = hparams["hash_bkts"]
    batch_size = hparams["batch_size"]
    train_data_path = hparams["train_data_path"]
    eval_data_path = hparams["eval_data_path"]
    num_evals = hparams["num_evals"]
    num_examples_to_train_on = hparams["num_examples_to_train_on"]
    output_dir = hparams["output_dir"]

    model_export_path = os.path.join(output_dir, "savedmodel")
    checkpoint_path = os.path.join(output_dir, "checkpoints")
    tensorboard_path = os.path.join(output_dir, "tensorboard")

    if tf.io.gfile.exists(output_dir):
        tf.io.gfile.rmtree(output_dir)

    model = build_dnn_model(num_bins, hash_bkts)
    logging.info(model.summary())

    trainds = create_train_dataset(train_data_path, batch_size)
    evalds = create_eval_dataset(eval_data_path, batch_size)

    steps_per_epoch = num_examples_to_train_on // (batch_size * num_evals)

    checkpoint_cb = callbacks.ModelCheckpoint(
        checkpoint_path, save_weights_only=True, verbose=1
    )
    tensorboard_cb = callbacks.TensorBoard(tensorboard_path, histogram_freq=1)

    history = model.fit(
        trainds,
        validation_data=evalds,
        epochs=num_evals,
        steps_per_epoch=max(1, steps_per_epoch),
        verbose=2,  # 0=silent, 1=progress bar, 2=one line per epoch
        callbacks=[checkpoint_cb, tensorboard_cb],
    )

    # Exporting the model with default serving function.
    model.save(model_export_path)
    return history
