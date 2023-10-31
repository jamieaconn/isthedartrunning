import rnn_functions
import matplotlib.pyplot as plt
import tensorflow as tf

parameters = {
    "num_steps": 80,
    "batch_size": 500,
    "state_size": 15,
    "learning_rate": 0.1,
    "num_epochs": 500,
    "num_level_updates": 40,
}

train_df, test_df = rnn_functions.load_data()

X, Y = rnn_functions.create_random_samples(train_df, parameters)
X_test, Y_test = rnn_functions.create_random_samples(test_df, parameters)

lstm_model = tf.keras.models.Sequential([
    # Shape [batch, time, features] => [batch, time, lstm_units]
    tf.keras.layers.LSTM(parameters["state_size"], return_sequences=True),
    # Shape => [batch, time, features]
    tf.keras.layers.Dense(units=1)
])

lstm_model.compile(loss=tf.keras.losses.MeanSquaredError(),
                optimizer=tf.keras.optimizers.legacy.Adam(),
                metrics=[tf.keras.metrics.MeanAbsoluteError()])

validation_data = (X_test, Y_test)

history = lstm_model.fit(x=X, y=Y, epochs=parameters["num_epochs"], validation_data = validation_data)

result_train = lstm_model.predict(X)
result_test = lstm_model.predict(X_test)

rnn_functions.plot_sample(X_test, Y_test, result_test, parameters)   

train_loss = history.history['loss']
val_loss = history.history['val_loss']

# Create a plot to show both training and validation loss over time
plt.figure()
plt.plot(train_loss, label='Training Loss')
plt.plot(val_loss, label='Validation Loss')
plt.title('Loss Over Time')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.savefig('loss_plot.png')
lstm_model.save('model.keras')