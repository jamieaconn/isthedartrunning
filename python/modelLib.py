import time
import json
import pandas as pd
import os
import numpy as np
import tensorflow as tf
import s3_functions
from logfuncts import logger
import sql_functions
from datetime import timedelta

FDIR = os.path.abspath(os.path.dirname(__file__))
RIVER_NAME = "dart"
OUTPUT_FILENAME = RIVER_NAME + ".json"
OUTPUT_PATH = os.path.join(FDIR, '../html', OUTPUT_FILENAME)

MIMIMUM_THRESHOLD = 0.7
MAXIMUM_THRESHOLD = 1.5

def rnn_model(testing_mode, testing_timestamp):
    model_parameters = {
        "num_level_updates": 40,
        "num_steps": 120,
    }

    if testing_mode:
        current_time = pd.to_datetime(testing_timestamp)
        df = sql_functions.load_dataframe_from_sql(river=RIVER_NAME, limit=-1)
        df = df[df.index > current_time - pd.Timedelta('2days')]
        df = df[df.index < current_time + pd.Timedelta('1days')]
        df.loc[(df.index > current_time - pd.Timedelta('1days')), "level"] = None
        df.loc[(df.index > current_time - pd.Timedelta('30minutes')), "cum_rain"] = None

    else:
        current_time = time.time()
        current_time = pd.to_datetime(current_time - (current_time % (15*60)), unit='s')
        df = sql_functions.load_dataframe_from_sql(river=RIVER_NAME, limit=200)
    
    logger.info("current_time: {value}".format(value=current_time))
    latest_level_update_timestamp = max(df[df.level.notnull()].index)
    latest_rain_time = max(df.index[df.cum_rain.notnull()])
    latest_forecast_rain_time = max(df.index[df.forecast.notnull()])
    logger.info("latest_level_update_timestamp: {value}".format(value=latest_level_update_timestamp))
    logger.info("latest_rain_time: {value}".format(value=latest_rain_time))
    logger.info("latest_forecast_rain_time: {value}".format(value=latest_forecast_rain_time))

    df = df[df.index <= latest_forecast_rain_time]

    # Fill in missing timestamps by reindexing
    min_time = min(df.index)
    max_time = max(df.index)
    rng = pd.date_range(min_time, max_time, freq='15Min')
    df = df.reindex(rng)

    # Remove rows after latest cum_rain value (no longer using forecast data) 
    #df = df[df.index <= latest_rain_time]

    # Convert cumulative rain to actual rain
    df['rain'] = df['cum_rain'].diff(periods=2)

    # negative values from diff are when the rain value resets so we set equal to the cumulative value
    df.loc[df['rain'] < 0, 'rain'] = df.loc[df['rain'] < 0, 'cum_rain']

    df['model_rain'] = pd.concat(
        (df[df.index <= latest_rain_time]["rain"],
        df[df.index > latest_rain_time]["forecast"])
    )
    # Interpolate model_rain

    df['model_rain'] = df['model_rain'].interpolate()
    df['model_rain'] = df['model_rain'].fillna(0)

    # filter to just have the required number of level updates
    df_model = df[df.index > latest_level_update_timestamp - timedelta(minutes=((model_parameters["num_level_updates"]) * 15))]

    # filter to just have the required number of steps
    df_model = df_model[:model_parameters["num_steps"]]

    x = df_model.model_rain.values         
    y = df_model.level.fillna(0).values
    timestamps = df_model.index.values

    update_vector = np.zeros(x.shape)
    update_vector[0:model_parameters["num_level_updates"]] = 1

    x = np.column_stack([x, update_vector, update_vector*y])
    x = np.reshape(x, (1, model_parameters["num_steps"], 3))
    y = np.column_stack([y])

    path_to_model = os.path.join(FDIR, "../modelling/model.keras")
    loaded_model = tf.keras.models.load_model(path_to_model)

    predict = np.squeeze(np.array(loaded_model(x)))

    # update
    num_rain_updates = model_parameters["num_steps"] - model_parameters["num_level_updates"]

    rain = np.concatenate((x[0,:num_rain_updates,0], np.zeros(x.shape[1] - num_rain_updates) * np.nan))
    forecast = np.concatenate((np.zeros(num_rain_updates) * np.nan, x[0,num_rain_updates:,0]))
    level = y[:,0]
    level[model_parameters["num_level_updates"]:] = None
    predict[:model_parameters["num_level_updates"]-1] = None

    # create output json
    output_df = pd.DataFrame({"timestamp":timestamps, "rain":rain, "forecast": forecast, "level":level, "predict": predict})

    output_df = output_df.round({'level': 3, 'predict': 3, 'rain' : 1, 'forecast': 1})
    output_df = pd.DataFrame(output_df).replace({np.nan:None})

    if latest_level_update_timestamp == current_time:
        current_level = output_df[output_df.timestamp == current_time]["level"].values[0]
    else:
        try:
            current_level = output_df[output_df.timestamp == current_time]["predict"].values[0]
        except:
            current_level = None

    logger.info('currenct level: ' + str(current_level))

    if current_level is None:
        text = "?"
    elif current_level > MAXIMUM_THRESHOLD:
        text = "THE DART IS MASSIVE"
    elif current_level > MIMIMUM_THRESHOLD:
        text = 'YES'
    elif output_df[(output_df.timestamp > current_time) & (output_df.timestamp < (current_time + pd.Timedelta('1hours')))]["predict"].max() > MIMIMUM_THRESHOLD:
        text = "THE DART WILL BE UP SHORTLY"
    else:
        text = 'NO'    

    logger.info("OUTPUT TEXT: " + text)

    output_df.timestamp = [timestamp.value / 1000 for timestamp in output_df.timestamp.tolist()]
    values = list(output_df.T.to_dict().values())

    output = {}       
    output['current_time'] = current_time.value / 1000
    output['current_level'] = current_level
    output['text'] = text
    output['values'] = values
    output['broken'] = False
    return(output)

def run(testing_mode=False):
    testing_timestamp = "2019-04-05 11:30:00" 
    output = rnn_model(testing_mode, testing_timestamp)    
    with open(OUTPUT_PATH, 'w') as f:
      json.dump(output, f, indent=4)
    if not testing_mode:
        s3_functions.upload_json_s3()

if __name__ == "__main__":
    run(testing_mode=True)

