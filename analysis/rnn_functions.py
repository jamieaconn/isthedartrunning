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

def load_data(start_date="2016-08-01 00:00:00", end_date = "2019-01-01 00:00:00"):
    df = modelLib.load_dataframe_from_sql("dart", limit=-1)
    
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
    plt.plot(df.model_rain)
    plt.plot(df.level)

    plt.xticks(rotation=90)
    plt.show()

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
            if random.randint(0, 10) > 4:
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
    num_level_updates = parameters["num_level_updates"]
    
    tf.reset_default_graph()
    x = tf.placeholder(tf.float32, [None, None, num_features], name='input_placeholder')
    y = tf.placeholder(tf.float32, [None, None], name='labels_placeholder')

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

    losses = tf.losses.mean_squared_error(y[num_level_updates:], predictions[num_level_updates:])
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


def run_training(train_df, parameters, graph, model_name):
    num_epochs = parameters["num_epochs"]
    batch_size = parameters["batch_size"]
    state_size = parameters["state_size"]
    num_epochs = parameters["num_epochs"]
    epoch_size = parameters["epoch_size"]
    
    train_step = graph["train_step"]
    total_loss = graph["total_loss"]
    final_state = graph["final_state"]
    losses = graph["losses"]
    predictions = graph["predictions"]
    x = graph["x"]
    y = graph["y"]
    
    init = tf.global_variables_initializer()
    with tf.Session() as sess:
        sess.run(init)
        training_losses = []
        Ys = []
        preds = []
        for idx in range(num_epochs):
            training_loss = 0
            training_state = np.zeros((batch_size, state_size))
            print "EPOCH", idx
            for step in range(epoch_size):
                X, Y = create_random_samples(train_df, parameters, rain_threshold=20)
                #print X.shape, Y.shape
                tr_losses, training_loss_, training_state, _, pred = \
                    sess.run([losses,
                              total_loss,
                              final_state,
                              train_step,
                              predictions],
                                  feed_dict={x:X, y:Y})
                training_loss += training_loss_
                
                if step % 50 == 0 and step > 0:
                    print("Average loss at step", step,
                          "for last 50 steps:", training_loss/50)
                    training_losses.append(training_loss/50)
                    training_loss = 0
                
                    
        cwd = os.getcwd()
        path = os.path.join(cwd, 'models', model_name)
        shutil.rmtree(path, ignore_errors=True)
                    
        tf.saved_model.simple_save(
            sess,
            path,
            inputs={"x": x, "y": y},
            outputs={"predictions": predictions}
        )

    return training_losses, X, Y, pred

def plot_sample(X, Y, pred, parameters, bucket_pred=False, index=False):
    if index:
        plt.plot(X[index,:,0], '-b', label='x')
        plt.plot(Y[index,:], '-m', label='y')
        plt.plot(pred[index,:], '-g', label='pred')
        plt.axvline(x=parameters["num_level_updates"], ymax=Y[index, parameters["num_level_updates"]], color='r', label='last level update')
        if bucket_pred is not False:
            plt.plot(bucket_pred[index], '-c', label='bucket_pred')

    else:
        plt.plot(X[:,0], '-b', label='x')
        plt.plot(Y, '-m', label='y')
        plt.plot(pred, '-g', label='pred')
        plt.axvline(x=parameters["num_level_updates"], ymax=Y[parameters["num_level_updates"]], color='r', label='last level update')
        if bucket_pred is not False:
            plt.plot(bucket_pred, '-c', label='bucket_pred')

    plt.legend(loc='upper right')
    plt.ylim(0, 2)
    plt.show()
    
    
def bucket_predict(inputs, num_level_updates):
    X = inputs["x"]
    pred = []
    for i in range(X.shape[0]):
        x = X[i,:,:]
        p = x[:, 2]
        starting_level = x[num_level_updates-1,2]
        # this fixes the math domain error that occurs for levels below modelLib.scale_a parameter
        if starting_level < modelLib.scale_a:
            starting_level = 0.265
        storage=modelLib.f_inv(modelLib.g_inv(starting_level))
    
        for j in range(x.shape[0]-num_level_updates):
            rain = x[j+num_level_updates,0]
            predict = modelLib.g(modelLib.f(storage))
            storage = storage + rain - modelLib.f(storage)
            p[j+num_level_updates] = predict
        pred.append(p)
    return np.array(pred)