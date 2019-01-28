import pandas as pd
import numpy as np
#%matplotlib inline
import matplotlib.pyplot as plt
import sqlite3
import os
import sys
import tensorflow as tf

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

def gen_real_data(df, update_timestep):
    X = np.array(list(df.model_rain.values))
    Y = np.array(list(df.level.values))
    # create a bool vector which is 1 for every update_timestep values else 0
    update_vector = np.array([1 if (val%update_timestep==0) else 0 for val in range(len(X))])
    X = np.column_stack([X, update_vector, update_vector*Y])
    return X, Y

def gen_batch(raw_data, batch_size, num_steps, num_features, epoch_size):
    # adapted from https://github.com/tensorflow/tensorflow/blob/master/tensorflow/models/rnn/ptb/reader.py
    #print "batch_size:", batch_size
    #print "num_steps:", num_steps
    raw_x, raw_y = raw_data
    data_length = raw_x.shape[0]
    num_features = raw_x.shape[1]
    
    #print "data_length:", data_length
    # partition raw data into batches and stack them vertically in a data matrix
    batch_partition_length = data_length // batch_size
    #print "batch_partition_length = data_length // batch_size = ", batch_partition_length

    data_x = np.zeros([batch_size, batch_partition_length, num_features], dtype=np.float32)
    data_y = np.zeros([batch_size, batch_partition_length], dtype=np.float32)
    for i in range(batch_size):
        data_x[i] = raw_x[batch_partition_length * i:batch_partition_length * (i + 1),:]
        data_y[i] = raw_y[batch_partition_length * i:batch_partition_length * (i + 1)]

    #print "data_x.shape, data_y.shape", data_x.shape, data_y.shape
    # further divide batch partitions into num_steps for truncated backprop
    for i in range(epoch_size):
        i = i % (batch_partition_length / num_steps)
        x = data_x[:, i * num_steps:(i + 1) * num_steps,:]
        y = data_y[:, i * num_steps:(i + 1) * num_steps]
        #print "x.shape, y.shape:", x.shape, y.shape
        yield (x, y)

    
def gen_epochs(num_epochs, num_steps, update_timestep, num_features, batch_size, df, epoch_size):
    for i in range(num_epochs):
        yield gen_batch(gen_real_data(df, update_timestep), batch_size, num_steps, num_features, epoch_size)
        
