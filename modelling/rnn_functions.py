import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import random

# local modules
module_path = os.path.abspath(os.path.join('../python'))
if module_path not in sys.path:
    sys.path.append(module_path)

import sql_functions
from logfuncts import logger

def load_data(start_date="2016-08-01 00:00:00", end_date = "2019-01-01 00:00:00"):
    df = sql_functions.load_dataframe_from_sql("dart", limit=-1)
    
    # Fill in missing timestamps by reindexing
    min_time = min(df.index)
    max_time = max(df.index)
    rng = pd.date_range(min_time, max_time, freq='15Min')
    df = df.reindex(rng)

    # Convert cumulative rain to actual rain
    df['rain'] = df['cum_rain'].diff(periods=2)

    # negative values from diff are when the rain value resets so we set equal to the cumulative value
    df.loc[df['rain'] < 0, 'rain'] = df.loc[df['rain'] < 0, 'cum_rain']

    # For training we always use the recorded rainfall rather than forecast
    df['model_rain'] = df['rain']

    # Interpolate model_rain

    df['model_rain'] = df['model_rain'].interpolate()
    df['model_rain'] = df['model_rain'].fillna(0)

    # take section of data for training
    df = df[(df.index>=start_date) & (df.index < end_date)]
    
    # some null values but let's just set them to base level 0.4
    df.level = df.level.fillna(method="pad")

    train_df = df.iloc[:int(df.shape[0]/2),:]
    test_df = df.iloc[int(df.shape[0]/2):,:]

    return train_df, test_df

def create_random_samples(df, parameters, rain_threshold=0):
    # rain threshold should be a value from 0 to 40
    num_level_updates = parameters["num_level_updates"]
    
    raw_X = np.array(list(df.model_rain.values))
    raw_Y = np.array(list(df.level.values))

    X = []
    Y = []
    while len(X) < parameters["batch_size"]:
        i = random.randint(0, raw_X.shape[0] - parameters["num_steps"])
        x = raw_X[i: i+parameters["num_steps"]]
        
        # This means we get fewer samples with no rain
        if sum(x) < rain_threshold:
            if random.randint(0, 10) > 4:
                continue
            
    
        y = raw_Y[i: i+parameters["num_steps"]]
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



def plot_sample(X, Y, pred, parameters, index=None):
    if not index:
        index = random.randint(0, X.shape[0])
    plt.figure()

    plt.plot(X[index,:,0], '-b', label='x')
    plt.plot(Y[index,:], '-m', label='y')
    plt.plot(pred[index,:], '-g', label='pred')
    plt.axvline(x=parameters["num_level_updates"], ymax=Y[index, parameters["num_level_updates"]], color='r', label='last level update')


    plt.legend(loc='upper right')
    plt.ylim(0, 2)
    plt.savefig('plot.png')
