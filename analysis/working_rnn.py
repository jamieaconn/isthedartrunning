import numpy as np
import tensorflow as tf
%matplotlib inline
import matplotlib.pyplot as plt

num_steps = 10
batch_size = 200
num_classes = 2
state_size = 15
learning_rate = 0.1



def gen_data(size=1000000):
    X = np.array(np.random.uniform(size=(size,)))
    Y = []
    for i in range(size):
        Y.append(0.5 * X[i-3] + 0.5 * X[i-8])
    return X, np.array(Y)

# adapted from https://github.com/tensorflow/tensorflow/blob/master/tensorflow/models/rnn/ptb/reader.py
def gen_batch(raw_data, batch_size, num_steps):
    raw_x, raw_y = raw_data
    data_length = len(raw_x)

    # partition raw data into batches and stack them vertically in a data matrix
    batch_partition_length = data_length // batch_size
    data_x = np.zeros([batch_size, batch_partition_length], dtype=np.float32)
    data_y = np.zeros([batch_size, batch_partition_length], dtype=np.float32)
    for i in range(batch_size):
        data_x[i] = raw_x[batch_partition_length * i:batch_partition_length * (i + 1)]
        data_y[i] = raw_y[batch_partition_length * i:batch_partition_length * (i + 1)]
    # further divide batch partitions into num_steps for truncated backprop
    epoch_size = batch_partition_length // num_steps

    for i in range(epoch_size):
        x = data_x[:, i * num_steps:(i + 1) * num_steps]
        y = data_y[:, i * num_steps:(i + 1) * num_steps]
        yield (x, y)

def gen_epochs(num_epochs, num_steps):
    for i in range(num_epochs):
        yield gen_batch(gen_data(), batch_size, num_steps)
        
        
        
        
"""
Placeholders
"""

x = tf.placeholder(tf.float32, [batch_size, num_steps], name='input_placeholder')
y = tf.placeholder(tf.float32, [batch_size, num_steps], name='labels_placeholder')
init_state = tf.zeros([batch_size, state_size])

"""
RNN Inputs
"""

# Turn our x placeholder into a list of one-hot tensors:
# rnn_inputs is a list of num_steps tensors with shape [batch_size, num_classes]
#x_one_hot = tf.one_hot(x, num_classes)
rnn_inputs = tf.unstack(tf.reshape(x, (x.shape[0], x.shape[1], 1)), axis=1)

print x
print
print rnn_inputs






"""
Definition of rnn_cell

This is very similar to the __call__ method on Tensorflow's BasicRNNCell. See:
https://github.com/tensorflow/tensorflow/blob/master/tensorflow/contrib/rnn/python/ops/core_rnn_cell_impl.py#L95
"""
with tf.variable_scope('rnn_cell'):
    W = tf.get_variable('W', [1 + state_size, state_size])
    b = tf.get_variable('b', [state_size], initializer=tf.constant_initializer(0.0))
    #Wy = tf.get_variable('Wy', [state_size, state_size])
    #by = tf.get_variable('by', [state_size], initializer=tf.constant_initializer(0.0))
    Wy = tf.get_variable('Wy', [state_size, 1])
    by = tf.get_variable('by', [1], initializer=tf.constant_initializer(0.0))
    
def rnn_cell(rnn_input, state):
    print "rnn_input", rnn_input.shape
    print "state", state.shape
    with tf.variable_scope('rnn_cell', reuse=True):
        W = tf.get_variable('W', [1 + state_size, state_size])
        print "W", W.shape
        b = tf.get_variable('b', [state_size], initializer=tf.constant_initializer(0.0))
        #Wy = tf.get_variable('Wy', [state_size, state_size])
        #by = tf.get_variable('by', [state_size], initializer=tf.constant_initializer(0.0))
        Wy = tf.get_variable('Wy', [state_size, 1])
        by = tf.get_variable('by', [1], initializer=tf.constant_initializer(0.0))
        state = tf.tanh(tf.matmul(tf.concat([rnn_input, state], 1), W) + b)
        #output = tf.tanh(tf.matmul(state, Wy) + by)
        output = tf.matmul(state, Wy) + by
    return state, output


"""
Adding rnn_cells to graph

This is a simplified version of the "static_rnn" function from Tensorflow's api. See:
https://github.com/tensorflow/tensorflow/blob/master/tensorflow/contrib/rnn/python/ops/core_rnn.py#L41
Note: In practice, using "dynamic_rnn" is a better choice that the "static_rnn":
https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/ops/rnn.py#L390
"""
state = init_state
rnn_outputs = []
for rnn_input in rnn_inputs:
    state, output = rnn_cell(rnn_input, state)
    rnn_outputs.append(output)
final_state = state





"""
Predictions, loss, training step

Losses is similar to the "sequence_loss"
function from Tensorflow's API, except that here we are using a list of 2D tensors, instead of a 3D tensor. See:
https://github.com/tensorflow/tensorflow/blob/master/tensorflow/contrib/seq2seq/python/ops/loss.py#L30
"""


predictions = tf.squeeze(rnn_outputs)

# Turn our y placeholder into a list of labels
y_as_list = tf.unstack(y, num=num_steps, axis=1)


#losses and train_step

#losses = [tf.nn.sparse_softmax_cross_entropy_with_logits(labels=label, logits=logit) for \
          #logit, label in zip(logits, y_as_list)

losses = tf.losses.mean_squared_error(y_as_list, predictions)
total_loss = tf.reduce_mean(losses)
train_step = tf.train.AdagradOptimizer(learning_rate).minimize(total_loss)



"""
Train the network
"""

def train_network(num_epochs, num_steps, state_size, verbose=True):
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        training_losses = []
        for idx, epoch in enumerate(gen_epochs(num_epochs, num_steps)):
            training_loss = 0
            training_state = np.zeros((batch_size, state_size))
            
            if verbose:
                print "EPOCH", idx
            for step, (X, Y) in enumerate(epoch):
                tr_losses, training_loss_, training_state, _, y_test, pred_test = \
                    sess.run([losses,
                              total_loss,
                              final_state,
                              train_step,
                              y_as_list,
                              predictions],
                                  feed_dict={x:X, y:Y, init_state:training_state})
                training_loss += training_loss_
                
            
                if step % 100 == 0 and step > 0:
                    if verbose:
                        print("Average loss at step", step,
                              "for last 250 steps:", training_loss/100)
                    training_losses.append(training_loss/100)
                    training_loss = 0
            
    return training_losses, X, Y, pred_test

training_losses, final_X, final_Y, final_predictions = train_network(3,num_steps, state_size)
plt.plot(training_losses)




plt.plot(final_predictions.T[-1])
plt.plot(final_X[-1])
plt.plot(final_Y[-1])
plt.show()