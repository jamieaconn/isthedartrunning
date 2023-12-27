# 1. load data (ea, dartcom, metoffice)
# 2. processing
# 3. run model
# 4. output results to file

import pandas as pd
import numpy as np
import tensorflow as tf
import datetime
from google.cloud import firestore

MIMIMUM_THRESHOLD = 0.7
MAXIMUM_THRESHOLD = 1.5

def round_down_to_15_minutes(d):
    rounded_datetime = d - datetime.timedelta(minutes=d.minute % 15, seconds=d.second, microseconds=d.microsecond)
    return(rounded_datetime)

def query_firestore(collection, start_datetime, end_datetime):
    db = firestore.Client()
    collection_ref = db.collection(collection)
        # Query Firestore for documents where timestamp is greater than current time
    query = collection_ref.where('timestamp', '>', start_datetime).where('timestamp', '<', end_datetime).stream()

    data_list = []
    for doc in query:
        data = doc.to_dict()
        data_list.append(data)
    return(pd.DataFrame(data_list))

def load_data(start_datetime, end_datetime):
    # Load data from the database and return a pandas dataframe. 

    rainfall_df = query_firestore('rainfall_data', start_datetime, end_datetime)
    level_df = query_firestore('level_data', start_datetime, end_datetime)
    metoffice_df = query_firestore('forecast_data', start_datetime, end_datetime)

    # processing
    rainfall_df['timestamp'] = rainfall_df['timestamp'].apply(round_down_to_15_minutes)
    rainfall_df = rainfall_df.groupby('timestamp')['rainfall'].first().reset_index()

    # join...
    timestamps = pd.date_range(start=start_datetime, end=end_datetime, freq='15T', tz='UTC')
    df = pd.DataFrame({'timestamp': timestamps})
    df = pd.merge(df, rainfall_df, on='timestamp', how='left')
    df = pd.merge(df, level_df, on='timestamp', how='left')
    df = pd.merge(df, metoffice_df, on='timestamp', how='left')

    cols = {
        'timestamp': 'timestamp',
        'rainfall': 'cum_rain',
        'level': 'level',
        'forecast_rainfall': 'forecast'
    }
    df.rename(columns=cols, inplace=True)
    df = df[list(cols.values())]

    df = df.set_index('timestamp')
    df = df.sort_index()

    return df


def run_model(requests):
    model_parameters = {
        "num_level_updates": 40,
        "num_steps": 120,
    }

    current_time = round_down_to_15_minutes(datetime.datetime.now())
    start_datetime = current_time - datetime.timedelta(days=1)
    end_datetime = current_time + datetime.timedelta(days=2)
    df = load_data(start_datetime, end_datetime)

    print("current_time: {value}".format(value=current_time))
    latest_level_update_timestamp = max(df[df.level.notnull()].index)
    latest_rain_time = max(df.index[df.cum_rain.notnull()])
    latest_forecast_rain_time = max(df.index[df.forecast.notnull()])
    print("latest_level_update_timestamp: {value}".format(value=latest_level_update_timestamp))
    print("latest_rain_time: {value}".format(value=latest_rain_time))
    print("latest_forecast_rain_time: {value}".format(value=latest_forecast_rain_time))

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
    df_model = df[df.index > latest_level_update_timestamp - datetime.timedelta(minutes=((model_parameters["num_level_updates"]) * 15))]

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

    path_to_model = "model.keras"
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

    print('currenct level: ' + str(current_level))

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

    print("OUTPUT TEXT: " + text)

    output_df.timestamp = [timestamp.value / 1000 for timestamp in output_df.timestamp.tolist()]
    values = list(output_df.T.to_dict().values())

    db = firestore.Client()
    
    collection_ref = db.collection('results_graph')
    # remove previous graph_data
    for doc in collection_ref.stream():
        doc.reference.delete()
    
    # add new graph_data
    for data_dict in values:
        collection_ref.add(data_dict)

    # update results document (with key values)
    document_ref = db.collection('results').document('results')
    document_ref.set(
        {
            'text': text,
            'current_level': current_level,
            'current_time': datetime.datetime.timestamp(current_time) / 1000
        }
    )
    return('Complete')
