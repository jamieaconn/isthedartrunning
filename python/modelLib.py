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

# local modules
from logfuncts import logger


time_format = "%Y-%m-%dT%H:%M"


k = 0.07
scale_m = 1.943
scale_a = 0.263
delay = np.timedelta64(60, 'm') # 60 minutes

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

def preprocessing(df):
    """Reindex to include missing timestamps and create new column for actual rain from cumulative rain"""
    logger.debug("Fill in missing timestamps by reindexing")
    
    min_time = min(df.index)
    max_time = max(df.index)

    rng = pd.date_range(min_time, max_time, freq='15Min')
    df = df.reindex(rng)

    logger.debug("Convert cumulative rain to actual rain")

    df['rain'] = df['cum_rain'].diff(periods=2)

    # negative values from diff are when the rain value resets so we set equal to the cumulative value
    df.loc[df['rain'] < 0, 'rain'] = df.loc[df['rain'] < 0, 'cum_rain']

    
    latest_rain_time = max(df.index[df.cum_rain.notnull()])
    logger.info('latest rain update at: ' + str(latest_rain_time))

    logger.debug("Concat rain and forecast to create model_rain")

    df['model_rain'] = pd.concat([
        df[df.index <= latest_rain_time]['rain'],
        df[df.index > latest_rain_time]['forecast']
    ])

    logger.debug("interpolate model_rain")

    df['model_rain'] = df['model_rain'].interpolate()

    return df


def pre_model_checks(df, current_time):
    # Check that there is a level update in df
    if len(df[df.level.notnull()]) == 0:
        logger.warning("No level update - exiting")
        sys.exit()   
    # Check that there is a row for now or past now
    if len(df[df.index >= current_time]) == 0:
        logger.warning("Not enough data - exiting")
        sys.exit()

        
def model(df, from_latest_level=True):
    logger.info('*** RUNNING MODEL ***')
    if from_latest_level:
        # for running model from latest level update onwards
        starting_time = max(df.index[df.level.notnull()])
    else:
        # for running model on entire dataframe
        starting_time = df.index[df.level.notnull()][5]
    starting_level = df.loc[starting_time].level


    logger.info('Run model from: ' + str(starting_time))
    logger.info('Starting level update: ' + str(starting_level))


    df['storage'] = np.nan
    df['predict'] = np.nan

    # Calculate initial storage
    init_storage = f_inv(g_inv(starting_level))
    df.loc[starting_time, 'storage'] = init_storage
    storage = init_storage

    # Run iteration for indexes > latest_level_update
    df_model = df[(df.index > pd.Timestamp(starting_time))]

    for i,r in df_model.iterrows():
        rain = df.loc[i - delay, 'model_rain']
        predict = g(f(storage))
        storage = storage + rain - f(storage)
        df.loc[i, 'storage'] = storage
        df.loc[i, 'predict'] = predict

    return df


# # Create export dictionary
# 
# * Round model_rain, level and predict
# * Get current time rounded down to nearest 15 minutes
# * create output dict with the following properties
#     * values
#     * current_time
#     * current_level
#     * text
#     * next_up if in next hour

def model_export(df, current_time):
    # Round export columns
    df = df.round({'level': 3, 'predict': 3, 'model_rain' : 1})

    try:
        current_row = df.loc[pd.to_datetime(current_time, unit='s')]
        current_level = current_row['level']
        if np.isnan(current_level):
            current_level = current_row['predict']
    except KeyError:
        print "Can't find row in df that matches current time: "+ time.strftime(time_format, time.gmtime(current_time))
        current_level = None

    
    logger.info('currenct level: ' + str(current_level))

    df.timestamp = df.index
    df = df.where((pd.notnull(df)), None)
    timestamp_vals = [timestmp.value / 1000 for timestmp in df.index.tolist()]
    rain_vals = df.model_rain.tolist()
    level_vals = df.level.tolist()
    predict_vals = df.predict.tolist()
    values = []
    for n in range(0, len(timestamp_vals)):
        values.append({'timestamp' : timestamp_vals[n], 'rain' : rain_vals[n], 'level' : level_vals[n], 'predict' : predict_vals[n]})

    if current_level > 1.5:
        text = "THE DART IS MASSIVE"
    elif current_level > 0.7:
        text = 'YES'
    else:
        next_up = df[(df.index > current_time) & (df.index < current_time + delay) & (df.predict > 0.7)].index.min()
        if pd.isnull(next_up):
            text = 'NO'
        else:
            text = "THE DART WILL BE UP SHORTLY"    
    
    logger.info("OUTPUT TEXT: " + text)



    output = {}       
    output['current_time'] = current_time.value / 1000
    output['current_level'] = current_level 
    output['text'] = text
    output['values'] = values


    return output
# # Write export to json


def upload_export(testing, output):
    """Upload json file to webpage via ftp and then force fb to update cache"""
    filename = "dart.json"
    with open(os.path.join(FDIR, '../' + filename), 'w') as f:
        json.dump(output, f, indent=4)

    from local_info import ftp_url, ftp_pass, ftp_user, ftp_dir
    ftp = ftplib.FTP(ftp_url)
    ftp.login(ftp_user, ftp_pass)
    if ftp_dir is not None:
        ftp.cwd(ftp_dir)

    ftp.storbinary("STOR " + filename, open(os.path.join(FDIR, '../' + filename)), 1024)

    from local_info import facebook_access 
    
    r = requests.post("https://graph.facebook.com", data={'scrape': 'True', 'id' : '  http://isthedartrunning.co.uk/', 'access_token' : facebook_access})


def run(testing):
    start_time = time.time()

    # # Load data from sql database into pandas df

    df = load_dataframe_from_sql(river="dart", limit=130)

    df = preprocessing(df)

    # # Calculate important timestamps
    
    # current time rounded down to nearest 15 minutes
    current_time = time.time()
    current_time = pd.to_datetime(current_time - (current_time % (15*60)), unit='s')
    logger.info('Current_time: ' + str(current_time))
    

    # # Pre-model checks
    pre_model_checks(df, current_time)

    # run model
    df = model(df)

    # create export
    output = model_export(df, current_time)

    # upload export
    upload_export(testing, output)
    logger.debug("---%s seconds --- taken to run model" % (time.time() - start_time))

