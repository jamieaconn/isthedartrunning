Have a number of epochs (num-epochs) and at the start of each epoch you reset the training state

Each epoch has a number (epoch-size) of batches and at the end of each batch you update the weights

The batch is what you pass into sess.run

The batch is X, Y where X has dim [batch-size, num-steps, num-features] and Y has dim [batch-size, num-steps]


