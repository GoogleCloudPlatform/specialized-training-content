"""Data prep, train and evaluate DNN model."""

from functools import partial
import logging
import os

import numpy as np
import tensorflow as tf
from tensorflow.keras import callbacks, models
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
DEFAULTS = [[0],["na"],[0.0],["na"],[0.0],[0.0],["na"],[0.0],[0.0],[0]]

INPUT_COLS = [
    c for c in CSV_COLS if c != LABEL_COLUMN
]


def features_and_labels(row_data):
    label = row_data.pop(LABEL_COLUMN)
    return row_data, label

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


def create_train_dataset(pattern, batch_size):
    dataset = load_dataset(pattern, batch_size, num_repeat=None)
    return dataset.prefetch(1)


def create_adapt_dataset(pattern, batch_size):
    dataset = load_dataset(pattern, batch_size, num_repeat=1)
    return dataset.prefetch(1)


def create_eval_dataset(pattern, batch_size):
    dataset = load_dataset(pattern, batch_size, num_repeat=1)
    return dataset.prefetch(1)

def get_input_and_transform(ds, num_bins, hash_bkts):
    
    inputs = {}
 
    for col in INT_COLS:
        inputs[col] = Input(name=col, shape=(1,), dtype=tf.int32)
    for col in CAT_COLS:
        inputs[col] = Input(name=col, shape=(1,), dtype=tf.string)
    for col in FLOAT_COLS:
        inputs[col] = Input(name=col, shape=(1,), dtype=tf.float32)
    
    feature_ds = ds.map(lambda x, y: x)
    
    def _get_col(ds,col):
        return ds[col] 
    
    transformed = {}

    layer = IntegerLookup(output_mode='one_hot')
    logging.warn("Adapting 'step' IntegerLookup layer.")
    layer.adapt(feature_ds.map(partial(_get_col, col='step')), steps=100)
    transformed['step'] = layer(inputs['step'])
    
    layer = StringLookup(output_mode='one_hot')
    logging.warn("Adapting 'action' StringLookup layer.")
    layer.adapt(feature_ds.map(partial(_get_col, col='action')), steps=100)
    transformed['action'] = layer(inputs['action'])

    for col in FLOAT_COLS:
        layer = Discretization(num_bins=num_bins, output_mode='one_hot')
        logging.warn(f"Adapting {col} Discretization layer.")
        layer.adapt(feature_ds.map(partial(_get_col, col=col)), steps=100)
        # layer = CategoryEncoding(num_bins, output_mode='one_hot')
        transformed[col] = layer(inputs[col])

    for col in ['idOrig', 'idDest']:
        layer = Hashing(hash_bkts, output_mode='one_hot')
        transformed[col] = layer(inputs[col])
                                
    return inputs, transformed
                                 

def build_dnn_model(ds, num_bins, hash_bkts):
    
    inputs, transformed = get_input_and_transform(ds, num_bins, hash_bkts)
    dnn_inputs = Concatenate()(transformed.values())
    dnn_inputs = Flatten()(dnn_inputs)
    hid_1 = tf.keras.layers.Dense(64, activation='relu')(dnn_inputs)
    hid_2 = tf.keras.layers.Dense(32, activation='relu')(hid_1)
    hid_3 = tf.keras.layers.Dense(16, activation='relu')(hid_2)
    logit = tf.keras.layers.Dense(1, activation='sigmoid')(hid_3)  

    metrics = [tf.keras.metrics.BinaryAccuracy(),
               tf.keras.metrics.Precision(),
               tf.keras.metrics.Recall(),
               tf.keras.metrics.AUC(curve='PR')]

    model = tf.keras.Model(inputs=inputs, outputs=logit)
    model.compile(loss=tf.keras.losses.BinaryCrossentropy(from_logits=False), metrics=metrics)

    return model


def train_and_evaluate(hparams):

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
        
    trainds = create_train_dataset(train_data_path, batch_size)
    adaptds = create_adapt_dataset(train_data_path, batch_size)
    evalds = create_eval_dataset(eval_data_path, batch_size)
    
    model = build_dnn_model(adaptds, num_bins, hash_bkts)
    logging.info(model.summary())

    steps_per_epoch = num_examples_to_train_on // (batch_size * num_evals)

    checkpoint_cb = callbacks.ModelCheckpoint(
        checkpoint_path, save_weights_only=True, verbose=1
    )
    tensorboard_cb = callbacks.TensorBoard(tensorboard_path, histogram_freq=0)

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
