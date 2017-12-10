import math
import time
import sys
import json
import pandas as pd
import os
import ftplib
import numpy as np
import requests
import logging

# local modules
import modelLib

fdir = os.path.abspath(os.path.dirname(__file__))
database = os.path.join(fdir, '../data.db')

time_format = "%Y-%m-%dT%H:%M"


k = 0.07
scale_m = 1.943
scale_a = 0.263
delay = np.timedelta64(60, 'm') # 60 minutes

def f(x):
    return math.exp(k*x)
def g(x):
    return (scale_m * x) + scale_a
def f_inv(x):
    return math.log(x) / k
def g_inv(x):
    return (x - scale_a) / scale_m


def model(testing=False):
    start_time = time.time()
# Get current time rounded down to nearest 15 minutes
    current_time = time.time()
    current_time = current_time - (current_time % (15*60))
    current_time = pd.to_datetime(current_time, unit='s')


# # Load data from sql database into pandas df

    df = modelLib.load_dataframe_from_sql(river="dart", limit=130)
    

# # Set index to timestamp column as object
    df.timestamp = pd.to_datetime(df.timestamp)
    df = df.set_index('timestamp')
    df = df.sort_index()


# # Pre-model checks



# Check that there is a level update in df
    if len(df[df.level.notnull()]) == 0:
        logging.warning("No level update - exiting")
        sys.exit()   
# Check that there is a row for now or past now
    if len(df[df.index >= current_time]) == 0:
        logging.warning("Not enough data - exiting")
        sys.exit()

# # Calculate important timestamps


    latest_level_time = max(df.index[df.level.notnull()])

    latest_level = df.loc[latest_level_time].level


    latest_rain_time = max(df.index[df.cum_rain.notnull()])

    logging.info('latest level at: ' + str(latest_level_time))
    logging.info('latest level is: ' + str(latest_level))
    logging.info('latest rain update at: ' + str(latest_rain_time))


# # Fill in missing timestamps


    min_time = min(df.index)
    max_time = max(df.index)
    rng = pd.date_range(min_time, max_time, freq='15Min')
    df = df.reindex(rng)


# # Cumulative rain -> actual rain

    df['rain'] = df['cum_rain'].diff(periods=2)
    df.loc[df['rain'] < 0, 'rain'] = 0 
# interpolate and div 2 to get actual rain every 15 min
    df['rain'] = df['rain'].interpolate()
    df['rain'] = df['rain'] / 2

# multiply by 4 to get rain rate per hour
    df['rain'] = df['rain'] * 2
    df.loc[(df.index > latest_rain_time), 'rain'] = 0



# # Interpolate forecast


# Input forecast data is in mm/hour



# Remove forecast before latest_rain_time
    df.loc[min_time:latest_rain_time, 'forecast'] = None

# Set forecast to rain at latest_rain_time
    df.loc[latest_rain_time].forecast = df.loc[latest_rain_time].rain

    df['forecast'] = df['forecast'].interpolate()



# # Run model


    df['model_rain'] = df['rain'].fillna(0) + df['forecast'].fillna(0)
    df['storage'] = np.nan
    df['predict'] = np.nan

# Calculate initial storage
    init_storage = f_inv(g_inv(latest_level))
    df.loc[latest_level_time, 'storage'] = init_storage

# Run iteration for indexes > latest_level_update
    storage = init_storage

# Remove forecast from the model
    df_model = df[(df.index > pd.Timestamp(latest_level_time))]

    #df_model = df[(df.index > pd.Timestamp(latest_level_time))]
    for i,r in df_model.iterrows():
        rain = df.loc[i - delay, 'model_rain']
        predict = g(f(storage))
        storage = storage + rain - f(storage)
        df.loc[i, 'storage'] = storage
        df.loc[i, 'predict'] = predict


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

    
    logging.info('currenct level: ' + str(current_level))

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
    
    logging.info("OUTPUT TEXT:", text)



    output = {}       
    output['current_time'] = current_time.value / 1000
    output['current_level'] = current_level 
    output['text'] = text
    output['values'] = values

    
    logging.info("---%s seconds ---" % (time.time() - start_time))
    return output
# # Write export to json


def upload_json(testing, output, filename):
    with open(os.path.join(fdir, '../' + filename), 'w') as f:
        json.dump(output, f, indent=4)

    from local_info import ftp_url, ftp_pass, ftp_user, ftp_dir
    ftp = ftplib.FTP(ftp_url)
    ftp.login(ftp_user, ftp_pass)
    if ftp_dir is not None:
        ftp.cwd(ftp_dir)

    ext = os.path.splitext(filename)[1]
    if ext in (".txt", ".htm", ".html"):
        ftp.storlines("STOR " + filename, open(os.path.join(fdir, '../' + filename)))
    else:
        ftp.storbinary("STOR " + filename, open(os.path.join(fdir, '../' + filename)), 1024)

def post_facebook():
    from local_info import facebook_access 
    
    r = requests.post("https://graph.facebook.com", data={'scrape': 'True', 'id' : '  http://isthedartrunning.co.uk/', 'access_token' : facebook_access})



def run_model(testing=False):
    output = model()
    filename = 'dart.json'
    upload_json(testing, output, filename)
    post_facebook()




def main():
    run_model(True)
    

if __name__ == "__main__":
    main()
