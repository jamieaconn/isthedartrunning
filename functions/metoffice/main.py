import requests 
from datetime import datetime, timedelta
from tokens import clientId, secret, orderName
import pygrib
import numpy as np

from google.cloud import firestore

# FileIds are in the format: total_precipitation_rate_ts3_+00 or total_precipitation_rate_ts26_+12
# ts3_00 means it's the forecast image for 3 hours after the midnight run
# There are also fileIds in the format: total_precipitation_rate_ts0_2023121800 which seem to be duplicates?
# General approach is to find out the latest run and then get all of the images for that run

#clientId = os.environ.get('metofficeClientId')
#secret = os.environ.get('metofficeSecret')
#orderName = os.environ.get('metofficeOrderName')

baseUrl = "https://api-metoffice.apiconnect.ibmcloud.com/1.0.0"
bucket_name = 'metoffice_forecast_images'

def get_runtimes():
    requestHeaders = {"x-ibm-client-id": clientId, "x-ibm-client-secret": secret, "Accept": "application/json"}
    requrl = baseUrl + "/runs?sort=RUNDATETIME"
    req = requests.get(requrl, headers=requestHeaders)
    r = req.json()
    runDateTimes = [run['runDateTime'] for run in r['runs'][0]['completeRuns']]
    latestRunDateTime =  max(runDateTimes)
    latestFullRunDateTime = max([run for run in runDateTimes if datetime.strptime(run, '%Y-%m-%dT%H:%M:%SZ').hour in [0,12]])
    runtimes = list(set([latestFullRunDateTime, latestRunDateTime]))
    return(runtimes)

def upload_files(latestRunDateTime):
    db = firestore.Client()
    requrl = baseUrl + "/orders/{orderId}/latest".format(orderId=orderName)
    requestHeaders = {"x-ibm-client-id": clientId, "x-ibm-client-secret": secret, "Accept": "application/json"}
    req = requests.get(requrl, headers=requestHeaders)
    r = req.json()

    # filter to the latest run time + filter out the other longer fileIds (which are duplicates)
    fileIds = [f['fileId'] for f in r['orderDetails']['files'] if (f['runDateTime'] == latestRunDateTime) and (len(f['fileId']) < 60)]

    
    requestHeaders = {"x-ibm-client-id": clientId, "x-ibm-client-secret": secret}

    for fileId in fileIds:
        (run, time) = fileId[33:].split("_")
        # Convert timestamp string to datetime object
        timestamp = datetime.strptime(latestRunDateTime, '%Y-%m-%dT%H:%M:%SZ')
        # Add hours to the datetime object
        timestamp += timedelta(hours=int(time))

        # check if time is in the past
        if(timestamp < datetime.now()):
            continue

        hours_away = (timestamp-datetime.now()).total_seconds() / 3600
        # we use a maximum of 40 hours of forecast data
        if(hours_away > 40):
            continue

        requrl=baseUrl + "/orders/{orderId}/latest/{fileId}/data".format(orderId=orderName,fileId=fileId)
        response = requests.get(requrl, headers=requestHeaders)

        grb = pygrib.fromstring(response.content)
        data = grb.values
        data = data * 3600 # convert units to mm/h
        lat, lon = grb.latlons()
        # for some reason the lon values are 360 deg out?
        lon = lon - 360

        lat_range = [50.54028093201509, 50.61029020017267]
        lon_range = [-3.978019229686611, -3.8768901858773095]

        # create a mask with True values only within the lat and lon ranges
        mask = (lat > lat_range[0]) & (lat < lat_range[1]) & (lon > lon_range[0]) & (lon < lon_range[1])

        # apply the max and take a mean to get average rainfall rate in the catchment
        forecast_rainfall = np.sum(data * mask)/np.sum(mask)

        timestamp_string = datetime.strftime(timestamp, '%Y-%m-%dT%H:%M:%SZ')

        #write to firestore
        doc_ref = db.collection('forecast_data').document(timestamp_string)
        doc_ref.set({
            'timestamp': timestamp,
            'run': run,
            'time': time,
            'forecast_rainfall': forecast_rainfall
        })

        print(run, time, forecast_rainfall)

def upload_latest_run_files(request):
    runtimes = get_runtimes()
    for run in runtimes:
        upload_files(run)
    return('complete')
