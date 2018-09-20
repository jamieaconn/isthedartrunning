import pandas as pd
import numpy as np
#%matplotlib inline
import matplotlib.pyplot as plt
import sqlite3
import os
import sys
import random

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

def create_random_samples(df, num_samples=1000, num_steps=40, cutoff=0.03):
    raw_X = np.array(list(df.model_rain.values))
    raw_Y = np.array(list(df.level.values))

    X = []
    Y = []
    while len(X) < num_samples:
        i = random.randint(0, raw_X.shape[0] - num_steps)
        x = raw_X[i: i+num_steps]
        if sum(x) < cutoff:
            continue
            
    
        y = raw_Y[i: i+num_steps]
        update_vector = np.zeros(x.shape)
        update_vector[0:10] = 1
        update_vector * y
        
        x = np.column_stack([x, update_vector, update_vector*y])
        y = np.column_stack([y])

        X.append(x)
        Y.append(y)
    X = np.array(X)
    Y = np.array(Y)
    return X, Y
