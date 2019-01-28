## Statement of the problem

We want to predict the level of the River Dart in Devon, UK.
The river has a gauge which records the level every 15 minutes. However this data is usually only published once a day at 4am and the river can rise and fall within 8 hours.
Rainfall is an effective predictor of the level and there is a rain gauge high up in the catchment of the river. This is recorded and published every 30 minutes.

The aim is to create a model combining recent published level updates and rainfall upto the present time to predict river levels past 

# Example
Current time is 13:00
We have river level data from 00:00 to 04:00
We have rain data from 00:00 to 13:00
We want to predict the river level from 04:15 to 13:00

# Generating a random sample
* Take a random index
* Take a slice of 100 timesteps (each 15 minutes) from the dataframe starting at that index
* Set all level updates to 0 other than the first 15
* Create a third boolean feature representing if there is a level update (1 if there is a level update and 0 otherwise)

One option for trying in future might be to vary the total number of timesteps in each sample (more realistic of real life).
Another is to cherry pick samples where there is some rain.

# Options

1. Use only the rain data to make the prediction and use a weighted sum over e.g. the past 36 hours. However, this doesn't take into account new information when a level update is published. These weights can be found using a neural network approach.
It might be possible to extend this using the 3 generated features (rain, level update, boolean representing if there is a level update) 

2. Use an iterative model called a bucket model.
* The bucket (analagous to the catchment) has a certain volume 
* The rain flows into the bucket
* The flow from the bucket is a function of the volume in the bucket

3. Recurrent neural network
* 

## Notes

Have a number of epochs (num-epochs) and at the start of each epoch you reset the training state

Each epoch has a number (epoch-size) of batches and at the end of each batch you update the weights

The batch is what you pass into sess.run

The batch is X, Y where X has dim [batch-size, num-steps, num-features] and Y has dim [batch-size, num-steps]


## Help

https://github.com/keras-team/keras/issues/168
https://towardsdatascience.com/rnn-training-tips-and-tricks-2bf687e67527
http://environment.data.gov.uk/flood-monitoring/assets/demo/index.html

