import math
import time
import sys
import json
import pandas as pd
import os
import ftplib
import numpy as np
import requests
import sqlite3
import boto3
import tensorflow as tf

# local modules
from logfuncts import logger


time_format = "%Y-%m-%dT%H:%M"


k = 0.07
scale_m = 1.943
scale_a = 0.263
delay = np.timedelta64(60, 'm') # 60 minutes
delay_timesteps = 4
FDIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(FDIR, '../data.db')

def f(x):
    return math.exp(k*x)
def g(x):
    return (scale_m * x) + scale_a
def f_inv(x):
    return math.log(x) / k
def g_inv(x):
    return (x - scale_a) / scale_m

def load_dataframe_from_sql(river, limit=-1):
    """Load data from the database and return a pandas dataframe. 
    Limit param specifies number of rows returned. Default is to return all"""
    if limit > 0:
        logger.debug("loading df for river {river} from sql with row limit of {limit}".format(river=river, limit=limit))
    else:
        logger.debug("loading entire df for river {river} from sql".format(river=river))
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

def rnn_model(df):
    # Reindex to include missing timestamps and create new column for actual rain from cumulative rain

    num_steps = 80
    num_level_updates = 40

    current_time = time.time()
    current_time = pd.to_datetime(current_time - (current_time % (15*60)), unit='s')
    latest_level_update_timestamp = max(df[df.level.notnull()].index)
    latest_rain_time = max(df.index[df.cum_rain.notnull()])
    logger.info('latest rain update at: ' + str(latest_rain_time))

    # Remove rows after latest cum_rain value (no longer using forecast data) 
    df = df[df.index <= latest_rain_time]

    min_time = min(df.index)
    max_time = max(df.index)

    # Fill in missing timestamps by reindexing
    rng = pd.date_range(min_time, max_time + pd.Timedelta('2.5hours'), freq='15Min')
    df = df.reindex(rng)

    # Convert cumulative rain to actual rain
    df['rain'] = df['cum_rain'].diff(periods=2)

    # negative values from diff are when the rain value resets so we set equal to the cumulative value
    df.loc[df['rain'] < 0, 'rain'] = df.loc[df['rain'] < 0, 'cum_rain']

    df['model_rain'] = df["rain"]

    # Interpolate model_rain

    df['model_rain'] = df['model_rain'].interpolate()

    input_df = pd.concat((
        df[df.index <=latest_level_update_timestamp].tail(num_level_updates),
        df[df.index >latest_level_update_timestamp].tail(num_level_updates)
    ))

    x = input_df.model_rain.values         
    y = input_df.level.fillna(0).values
    timestamps = input_df.index.values

    # need to padd out input arrays with zeros to get the correct shape
    num_padding_steps = num_steps - x.shape[0] 
    x = np.concatenate((x, np.zeros(num_padding_steps)))
    y = np.concatenate((y, np.zeros(num_padding_steps)))   

    update_vector = np.zeros(x.shape)
    update_vector[0:num_level_updates] = 1

    x = np.column_stack([x, update_vector, update_vector*y])
    y = np.column_stack([y])

    model_name = "production_rnn"
    path_to_model = os.path.join(FDIR, model_name)
    predict_fn = tf.contrib.predictor.from_saved_model(path_to_model)
    predict = predict_fn({"x":[x]})["predictions"]

    # remove excess padding
    predict = predict[:-num_padding_steps]
    level = y[:-num_padding_steps,0]
    rain = x[:-num_padding_steps,0]

    # set levels after latest update and predicts before to None
    level[num_level_updates:] = None
    predict[:num_level_updates-1] = None

    # create output json
    output_df = pd.DataFrame({"timestamp":timestamps, "rain":rain, "level":level, "predict": predict})

    output_df = output_df.round({'level': 3, 'predict': 3, 'model_rain' : 1})
    output_df = pd.DataFrame(output_df).replace({np.nan:None})

    if latest_level_update_timestamp == current_time:
        current_level = output_df[output_df.timestamp == current_time]["level"].values[0]
    else:
        current_level = output_df[output_df.timestamp == current_time]["predict"].values[0]

    logger.info('currenct level: ' + str(current_level))

    minimum_threshold = 0.7
    massive_threshold = 1.5

    if current_level > massive_threshold:
        text = "THE DART IS MASSIVE"
    elif current_level > minimum_threshold:
        text = 'YES'
    elif output_df[output_df.timestamp > current_time]["predict"].max() > minimum_threshold:
        text = "THE DART WILL BE UP SHORTLY"
    else:
        text = 'NO'    

    logger.info("OUTPUT TEXT: " + text)

    output_df.timestamp = [timestamp.value / 1000 for timestamp in output_df.timestamp.tolist()]
    values = output_df.T.to_dict().values()

    output = {}       
    output['current_time'] = current_time.value / 1000
    output['current_level'] = float(current_level) 
    output['text'] = text
    output['values'] = values
    return output

def upload_export_s3(testing, output):
    from local_info import aws_access_key_id, aws_secret_access_key, region_name, bucket_name
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)
    filename="dart.json"
    print output
    with open(os.path.join(FDIR, '../' + filename), 'w') as f:
        json.dump(output, f, indent=4)
    
    with open(os.path.join(FDIR, '../' + filename)) as data:
        bucket.put_object(Key=filename, Body=data, ContentType="text/json")


def run(testing):
    start_time = time.time()

    # # Load data from sql database into pandas df

    df = load_dataframe_from_sql(river="dart", limit=130)

    output = rnn_model(df)    

    # upload export
    #upload_export(testing, output)
    upload_export_s3(testing, output)
    logger.debug("---%s seconds --- taken to run model" % (time.time() - start_time))

