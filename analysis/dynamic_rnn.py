# based on https://r2rt.com/recurrent-neural-networks-in-tensorflow-i.html

import pandas as pd
import numpy as np
#%matplotlib inline
import matplotlib.pyplot as plt
import sqlite3
import os
import sys
import tensorflow as tf
import warnings

from rnn_functions import *


# Parameters
num_steps = 40
batch_size = 150
state_size = 15
learning_rate = 0.1
update_timestep = 100
num_epochs = 20
num_features = 3
epoch_size = 200

train_df, test_df = load_data()

tf.reset_default_graph()

x = tf.placeholder(tf.float32, [batch_size, num_steps, num_features], name='input_placeholder')
y = tf.placeholder(tf.float32, [batch_size, num_steps], name='labels_placeholder')
init_state = tf.zeros([batch_size, state_size])
cell = tf.contrib.rnn.BasicRNNCell(state_size)

rnn_inputs = x
rnn_outputs, final_state = tf.nn.dynamic_rnn(cell, rnn_inputs, initial_state=init_state)
rnn_outputs = tf.layers.dense(rnn_outputs, 1)

# remove dimension equal to 1
predictions = tf.squeeze(rnn_outputs)

losses = tf.losses.mean_squared_error(y, predictions)
total_loss = tf.reduce_mean(losses)
train_step = tf.train.AdagradOptimizer(learning_rate).minimize(total_loss)

verbose=True
with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    training_losses = []
    Ys = []
    preds = []
    for idx, epoch in enumerate(gen_epochs(num_epochs, num_steps, update_timestep, num_features, batch_size, train_df, epoch_size)):
        training_loss = 0
        training_state = np.zeros((batch_size, state_size))

        if verbose:
            print "EPOCH", idx
        for step, (X, Y) in enumerate(epoch):
            #print X.shape, Y.shape
            tr_losses, training_loss_, training_state, _, pred = \
                sess.run([losses,
                          total_loss,
                          final_state,
                          train_step,
                          predictions],
                              feed_dict={x:X, y:Y, init_state:training_state})
            training_loss += training_loss_
            preds += list(pred.T[-1])
            Ys += list(Y.T[-1])
            if step % 50 == 0 and step > 0:
                if verbose:
                    print("Average loss at step", step,
                          "for last 50 steps:", training_loss/50)
                training_losses.append(training_loss/50)
                training_loss = 0

plt.plot(training_losses)
plt.show()

plt.plot(preds[-200:])
plt.plot(Ys[-200:])
plt.savefig('graph.png', dpi=400)
plt.show()

from math import sqrt

errors = np.abs(np.array(Ys) - np.array(predictions))
print "Mean absolute error:", errors.mean().round(4)
print "Root mean squared error:", round(sqrt((errors ** 2).mean()), 3)

# with tf.Session() as sess:
#     preds = []
#     Ys = []
#     sess.run(tf.global_variables_initializer())
#     for idx, epoch in enumerate(gen_epochs(5, num_steps, update_timestep, num_features, batch_size, df)):    
#         training_state = np.zeros((batch_size, state_size))
#         if verbose:
#             print "EPOCH", idx
#         for step, (X, Y) in enumerate(epoch):
#             pred = sess.run(predictions, feed_dict={x:X, y:Y, init_state:training_state})
#             preds += list(pred[-1])
#             Ys += list(Y[-1])

# errors = np.abs(np.array(Ys) - np.array(preds))
# print "Mean absolute error:", errors.mean().round(4)
# print "Root mean squared error:", round(sqrt((errors ** 2).mean()), 3)