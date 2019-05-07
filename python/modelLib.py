import math
import time
import json
import pandas as pd
import os
import numpy as np
import sqlite3
import boto3
import tensorflow as tf

from logfuncts import logger

FDIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(FDIR, '../data.db')
RIVER_NAME = "dart"
OUTPUT_FILENAME = RIVER_NAME + ".json"
OUTPUT_PATH = os.path.join(FDIR, '../html', OUTPUT_FILENAME)

MIMIMUM_THRESHOLD = 0.7
MAXIMUM_THRESHOLD = 1.5

def load_dataframe_from_sql(river, limit=-1):
    """Load data from the database and return a pandas dataframe. 
    Limit param specifies number of rows returned. Default is to return all"""
    if limit > 0:
        logger.info("loading df for river {river} from sql with row limit of {limit}".format(river=river, limit=limit))
    else:
        logger.info("loading entire df for river {river} from sql".format(river=river))
    con = sqlite3.connect(DATABASE_PATH)
    cur = con.cursor()
    query = """
            SELECT timestamp, rain, level, forecast 
                from {river}
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
    cur.execute(query.format(river=river, limit=limit))
    result = cur.fetchall()

    df = pd.DataFrame(result, columns=['timestamp', 'cum_rain', 'level', 'forecast'])
    # # Set index to timestamp column as object
    df.timestamp = pd.to_datetime(df.timestamp)
    df = df.set_index('timestamp')
    df = df.sort_index()

    return df

def rnn_model(testing_mode, testing_timestamp):
    if testing_mode:
        current_time = pd.to_datetime(testing_timestamp)
        df = load_dataframe_from_sql(river=RIVER_NAME, limit=-1)
        df = df[df.index > current_time - pd.Timedelta('2days')]
        df = df[df.index < current_time + pd.Timedelta('1days')]
        df.loc[(df.index > current_time - pd.Timedelta('1days')), "level"] = None
        df.loc[(df.index > current_time - pd.Timedelta('30minutes')), "cum_rain"] = None

    else:
        current_time = time.time()
        current_time = pd.to_datetime(current_time - (current_time % (15*60)), unit='s')
        df = load_dataframe_from_sql(river=RIVER_NAME, limit=130)
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

    num_level_updates = df[df.index <= latest_level_update_timestamp].shape[0]
    num_rain_updates = df[df.index <= latest_rain_time].shape[0]
    num_forecast_rain_updates = df[df.index <= latest_forecast_rain_time].shape[0]

    logger.info("num_level_updates: {value}".format(value=num_level_updates))
    logger.info("num_rain_updates: {value}".format(value=num_rain_updates))
    logger.info("num_forecast_rain_updates: {value}".format(value=num_forecast_rain_updates))


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

    x = df.model_rain.values         
    y = df.level.fillna(0).values
    timestamps = df.index.values

    update_vector = np.zeros(x.shape)
    update_vector[0:num_level_updates] = 1

    x = np.column_stack([x, update_vector, update_vector*y])
    y = np.column_stack([y])

    model_name = "production_rnn"
    path_to_model = os.path.join(FDIR, model_name)
    predict_fn = tf.contrib.predictor.from_saved_model(path_to_model)
    predict = predict_fn({"x":[x]})["predictions"]
    
    rain = np.concatenate((x[:num_rain_updates,0], np.zeros(x.shape[0] - num_rain_updates) * np.nan))
    forecast = np.concatenate((np.zeros(num_rain_updates) * np.nan, x[num_rain_updates:,0]))
    level = y[:,0]
    level[num_level_updates:] = None
    predict[:num_level_updates-1] = None

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
    values = output_df.T.to_dict().values()

    output = {}       
    output['current_time'] = current_time.value / 1000
    output['current_level'] = current_level
    output['text'] = text
    output['values'] = values
    return output

def upload_export_s3():
    from local_info import aws_access_key_id, aws_secret_access_key, region_name, bucket_name
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)
    with open(os.path.join(OUTPUT_PATH)) as data:
        bucket.put_object(Key=OUTPUT_FILENAME, Body=data, ContentType="text/json")


def run(testing_mode=False):
    testing_timestamp = "2019-04-05 11:30:00" 
    output = rnn_model(testing_mode, testing_timestamp)    
    with open(OUTPUT_PATH, 'w') as f:
      json.dump(output, f, indent=4)
    if not testing_mode:
        upload_export_s3()

if __name__ == "__main__":
    run(testing_mode=True)

