import requests 
from datetime import datetime, timedelta
from tokens import apiKey, orderName
import pygrib
import numpy as np

from google.cloud import firestore

baseUrl = "https://data.hub.api.metoffice.gov.uk/atmospheric-models/1.0.0"
bucket_name = 'metoffice_forecast_images'

db = firestore.Client()

def get_runtimes():
    requestHeaders = {"apiKey": apiKey, "Accept": "application/json"}
    requrl = baseUrl + "/runs?sort=RUNDATETIME"
    req = requests.get(requrl, headers=requestHeaders)
    r = req.json()
    runDateTimes = [run['runDateTime'] for run in r['runs'][0]['completeRuns']]
    latestRunDateTime =  max(runDateTimes)
    latestFullRunDateTime = max([run for run in runDateTimes if datetime.strptime(run, '%Y-%m-%dT%H:%M:%SZ').hour in [0,12]])
    runtimes = list(set([latestFullRunDateTime, latestRunDateTime]))
    return(runtimes)

def calculate_rainfall(data):
    grb = pygrib.fromstring(data)
    data = grb.values
    data = data * 3600 # convert units to mm/h
    lat, lon = grb.latlons()

    lat_range = [50.457504, 50.635526]
    lon_range = [-4.026476 + 360, -3.746338 + 360]

    # create a mask with True values only within the lat and lon ranges
    mask = (lat > lat_range[0]) & (lat < lat_range[1]) & (lon > lon_range[0]) & (lon < lon_range[1])

    # apply the max and take a mean to get average rainfall rate in the catchment
    forecast_rainfall = np.sum(data * mask)/np.sum(mask)
    return(forecast_rainfall)

def list_files(runtimes):
    requrl = baseUrl + "/orders/{orderId}/latest".format(orderId=orderName)
    requestHeaders = {"apiKey": apiKey, "Accept": "application/json"}
    req = requests.get(requrl, headers=requestHeaders)
    r = req.json()

    # filter to the latest run time + filter out the other longer fileIds (which are duplicates)
    fileIds = [f['fileId'] for f in r['orderDetails']['files'] if (f['runDateTime'] in runtimes) and (len(f['fileId']) > 40)]

    files = []
    for fileId in fileIds:
        (run, time) = fileId[32:].split("_")
        # Convert timestamp string to datetime object
        timestamp = datetime.strptime(run, '%Y%m%d%H')
        # Add hours to the datetime object
        timestamp += timedelta(hours=int(time))

        files.append({
            'fileId': fileId,
            'timestamp': timestamp,
            'run': run,
            'time': time   
        })
    return(files)

def upload_files(files):
    # sort the list (want to process more recent runs first and times closest into the future)
    files = sorted(files, key=lambda x: (-int(x['run']), int(x['time'])))

    # skip if already in firestore
    docs = db.collection("forecast_data").where('timestamp', '>', datetime.now())
    existing_files = [doc.to_dict() for doc in docs.get()]
    existing_files = [{'run': f['run'], 'time':f['time'], 'timestamp': datetime.strptime(f['run'], '%Y%m%d%H') + timedelta(hours=int(f['time']))} for f in existing_files]
    
    i = 1
    for file in files:
        # limit queries to 10 per run
        if i > 10:
            break

        # skip if time is in the past
        if file['timestamp'] < datetime.now():
            continue
        
        # skip if more than 40 hours into the future
        if (file['timestamp'] - datetime.now()).total_seconds() / 3600 > 40:
            continue

        
        # if exact request has previously done or there's a newer run for same timestamp continue...

        existing_files_this_timestamp = [f['run'] for f in existing_files if f['timestamp'] == file['timestamp']]

        if len(existing_files_this_timestamp) != 0:
            if max(existing_files_this_timestamp) >= file['run']:
                print(file['timestamp'],'Skipped as already same or more recent run')
                continue

        requestHeaders = {"apiKey": apiKey}
        requrl=baseUrl + "/orders/{orderId}/latest/{fileId}/data".format(orderId=orderName,fileId=file['fileId'])
        response = requests.get(requrl, headers=requestHeaders)
    
        forecast_rainfall = calculate_rainfall(response.content)
        file['forecast_rainfall'] = forecast_rainfall
        
        timestamp_string = datetime.strftime(file['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
        doc_ref = db.collection('forecast_data').document(timestamp_string)
        
        doc_ref.set(file)

        print(file['run'], file['time'], forecast_rainfall)

        existing_files.append({key: file[key] for key in ['timestamp', 'run', 'time']})
        
        i = i+1

def upload_latest_run_files(request):
    runtimes = get_runtimes()
    files = list_files(runtimes)
    upload_files(files)
    return('complete')
