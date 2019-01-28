import pandas as pd
import numpy as np
#%matplotlib inline
import matplotlib.pyplot as plt
import sqlite3
import os
import sys
import random
import tensorflow as tf
import shutil

# local modules
module_path = os.path.abspath(os.path.join('../python'))
if module_path not in sys.path:
    sys.path.append(module_path)

import modelLib
from logfuncts import logger

def load_data():
    df = modelLib.load_dataframe_from_sql("dart", limit=-1)

    df = modelLib.preprocessing(df)

    # take a nice section 
    start_date = "2016-08-01 00:00:00"
    end_date = "2018-06-14 18:00:00"
    df = df[(df.index>=start_date) & (df.index < end_date)]

    # some null values but let's just set them to base level 0.4
    df.level = df.level.fillna(method="pad")
    train_df = df.iloc[:32772,:]
    test_df = df.iloc[32772:,:]

    return train_df, test_df

def create_random_samples(df, parameters, rain_threshold=0):
    # rain threshold should be a value from 0 to 40
    batch_size = parameters["batch_size"]
    num_level_updates = parameters["num_level_updates"]
    num_steps = parameters["num_steps"]
    
    raw_X = np.array(list(df.model_rain.values))
    raw_Y = np.array(list(df.level.values))

    X = []
    Y = []
    while len(X) < batch_size:
        i = random.randint(0, raw_X.shape[0] - num_steps)
        x = raw_X[i: i+num_steps]
        # This means we get fewer samples with no rain
        
        if sum(x) < rain_threshold:
            continue
            
    
        y = raw_Y[i: i+num_steps]
        update_vector = np.zeros(x.shape)
        update_vector[0:num_level_updates] = 1
        
        x = np.column_stack([x, update_vector, update_vector*y])
        y = np.column_stack([y])

        X.append(x)
        Y.append(y)
    X = np.array(X)
    Y = np.array(Y)
    Y = Y[:,:,0]
    return X, Y


def generate_graph(parameters):
    #print parameters
    
    num_steps = parameters["num_steps"]
    num_features = parameters["num_features"]
    state_size = parameters["state_size"]
    num_layers = parameters["num_layers"]
    learning_rate = parameters["learning_rate"]
    batch_size = parameters["batch_size"]
    
    tf.reset_default_graph()
    x = tf.placeholder(tf.float32, [None, num_steps, num_features], name='input_placeholder')
    y = tf.placeholder(tf.float32, [None, num_steps], name='labels_placeholder')

    rnn_inputs = x
    
    multi_cell = tf.nn.rnn_cell.MultiRNNCell([tf.nn.rnn_cell.LSTMCell(state_size, state_is_tuple=True) for _ in range(num_layers)], 
                                    state_is_tuple=True)

    #cell = tf.nn.rnn_cell.LSTMCell(state_size, state_is_tuple=False)
    #print cell
    #multi_cell = tf.nn.rnn_cell.MultiRNNCell([cell] * num_layers, state_is_tuple=False)
    #init_state = cell.zero_state(batch_size, tf.float32)
    
    rnn_outputs, final_state = tf.nn.dynamic_rnn(multi_cell, rnn_inputs, dtype=tf.float32)
    rnn_outputs = tf.layers.dense(rnn_outputs, 1)

    # remove dimension equal to 1
    predictions = tf.squeeze(rnn_outputs)

    losses = tf.losses.mean_squared_error(y, predictions)
    total_loss = tf.reduce_mean(losses)
    train_step = tf.train.AdagradOptimizer(learning_rate).minimize(total_loss)
    graph = {
        "train_step": train_step, 
        "total_loss": total_loss,
        "final_state": final_state,
        "losses": losses,
        "predictions": predictions,
        "x": x,
        "y": y,
    }
    return graph

def plot_sample(X, Y, pred, parameters, bucket_pred=False, index=False):
    if index:
        plt.plot(X[index,:,0], '-b', label='x')
        plt.plot(Y[index,:], '-m', label='y')
        plt.plot(pred[index,:], '-g', label='pred')
        plt.axvline(x=parameters["num_level_updates"], ymax=Y[index, parameters["num_level_updates"]], color='r', label='last level update')
        if bucket_pred is not None:
            plt.plot(bucket_pred[index], '-c', label='bucket_pred')

    else:
        plt.plot(X[:,0], '-b', label='x')
        plt.plot(Y, '-m', label='y')
        plt.plot(pred, '-g', label='pred')
        plt.axvline(x=parameters["num_level_updates"], ymax=Y[parameters["num_level_updates"]], color='r', label='last level update')
        if bucket_pred is not None:
            plt.plot(bucket_pred, '-c', label='bucket_pred')

    plt.legend(loc='upper right')
    plt.ylim(0, 2)
    plt.show()