#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 10:49:38 2017

@author: Yacalis
"""

print('Begin Cbrain Keras Program')
print('Importing Libraries, Packages, and Modules')

# =============================================================================
# NOTE: To properly set random seed for reproducible results, the code has to
# be limited to a single thread, and a separate chunk of code must be added to
# the top of this file. Detailed instructions are documented here:
# https://keras.io/getting-started/faq/#how-can-i-obtain-reproducible-results-
# using-keras-during-development
# =============================================================================

import keras  # MUST be imported before other keras imports - ignore IDE
import keras.backend as K
from keras.layers import Dense, Dropout, Activation
from keras.models import Sequential
from sklearn.model_selection import train_test_split

from cbrain_keras_callbacks import CustomCallbacks
from cbrain_keras_config import Config
from cbrain_keras_dataLoad import DataLoader
from cbrain_keras_folderDefs import get_logdir
from cbrain_keras_optimizer import Optimizer
from act_funcs import act_funcs
from loss_funcs import loss_funcs

# =============================================================================
# Get Data
# =============================================================================
print('Loading Data')

configuration = Config()
config = configuration.config
dataloader = DataLoader(config)
x_data = dataloader.x_data
y_data = dataloader.y_data

# =============================================================================
# Set Parameter Constants
# =============================================================================
print('Setting Parameters')

hidden_lays = list(map(int, config.hidden_lays.split(',')))
nhidden = len(hidden_lays)
hidden_lays_act = act_funcs[config.hidden_lays_act]
output_lay_act = act_funcs[config.output_lay_act]
loss_func = loss_funcs[config.loss_func]

# define data dims
input_dim = x_data.shape[1]
output_dim = y_data.shape[1]


# =============================================================================
# Metrics, Callback, Optimizer
# =============================================================================
print('Setting Up Metrics, Callbacks, and Optimizer')

metrics = config.metrics.split(',')


# add custom metric (same scalar that Pierre uses for "loss/logloss")
def log10_loss(y_true, y_pred):
    reg_loss = K.sqrt(K.mean(K.square(y_true - y_pred), axis=-1))
    log_loss = K.log(reg_loss + 1e-20) / K.log(10.0)
    return log_loss


def rsquared(y_true, y_pred):
    tot_err = K.reduce_sum(K.square(K.subtract(y_true, K.reduce_mean(y_true))))
    unexpl_err = K.reduce_sum(K.square(K.subtract(y_true, y_pred)))
    rsquare = K.subtract(1., K.divide(unexpl_err, tot_err))
    return rsquare


metrics.append(log10_loss)
metrics.append(rsquared)
log_dir = get_logdir(config)
callbacks = CustomCallbacks(config, log_dir).callbacks
optimizer = Optimizer(config).optimizer

# =============================================================================
# Build Model
# =============================================================================
print('Building Model')

# create layer arrangement
model = Sequential()

# add input layer and first hidden layer
model.add(Dense(hidden_lays[0], input_dim=input_dim))
model.add(Activation(hidden_lays_act))
if config.use_dropout:
    model.add(Dropout(config.dropout_rate))

# add any hidden layers after the first one
for layer in range(nhidden - 1):
    model.add(Dense(hidden_lays[layer + 1]))
    model.add(Activation(hidden_lays_act))
    if config.use_dropout:
        model.add(Dropout(config.dropout_rate))

# add output layer
model.add(Dense(output_dim))
model.add(Activation(output_lay_act))

# compile model
model.compile(loss=loss_func,
              optimizer=optimizer,
              metrics=metrics)

# =============================================================================
# Train Model
# =============================================================================
print('Training Model')

# split data into training and test sets
x_train, x_test, y_train, y_test = train_test_split(
    x_data, y_data, test_size=config.frac_test)

# train the model
model.fit(x_train,
          y_train,
          epochs=config.epochs,
          batch_size=config.batch_size,
          shuffle=config.shuffle,
          validation_split=config.valid_split,
          verbose=1,
          callbacks=callbacks)

# misc - save config data from run (can't do this sooner without more code)
configuration.save_config(config, log_dir)

print('Model Training Completed')
print('Score: ', model.evaluate(x_test, y_test, batch_size=config.batch_size))

print('Saving Model and Weights')
model_fp = log_dir + 'finished_model.h5'
weights_fp = log_dir + 'finished_weights.h5'
model.save(model_fp)
model.save_weights(weights_fp)

# =============================================================================
# NOTE: For instructions on how to load the saved model and/or weights, see:
# https://keras.io/getting-started/faq/#how-can-i-save-a-keras-model
# =============================================================================

print('End Cbrain Keras Program')