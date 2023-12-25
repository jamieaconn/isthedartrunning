import requests 
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta
import numpy as np
import os
from tokens import clientId, secret, orderName

from google.cloud import storage

# FileIds are in the format: total_precipitation_rate_ts3_+00 or total_precipitation_rate_ts26_+12
# ts3_00 means it's the forecast image for 3 hours after the midnight run
# There are also fileIds in the format: total_precipitation_rate_ts0_2023121800 which seem to be duplicates?
# General approach is to find out the latest run and then get all of the images for that run

#clientId = os.environ.get('metofficeClientId')
#secret = os.environ.get('metofficeSecret')
#orderName = os.environ.get('metofficeOrderName')

baseUrl = "https://api-metoffice.apiconnect.ibmcloud.com/metoffice/production/map-images/1.0.0"

requestHeaders = {"x-ibm-client-id": clientId, "x-ibm-client-secret": secret, "Accept": "application/json"}


def get_latest_runtime():
    requrl = baseUrl + "/runs?sort=RUNDATETIME"
    req = requests.get(requrl, headers=requestHeaders)
    r = req.json()
    latestRunDateTime = max([run['runDateTime'] for run in r['runs'][0]['completeRuns']])
    return(latestRunDateTime)


bucket_name = 'metoffice_forecast_images'

def upload_files(latestRunDateTime):
    url = baseUrl + "/orders/" + orderName + "/latest"
    req = requests.get(url, headers=requestHeaders)
    r = req.json()
    # filter to the latest run time + filter out the other longer fileIds (which are duplicates)
    fileIds = [f['fileId'] for f in r['orderDetails']['files'] if (f['runDateTime'] == latestRunDateTime) and (len(f['fileId']) < 35)]

    for fileId in fileIds:
        url = baseUrl + "/orders/" + orderName + "/latest/" + fileId + "/data"
        #url = url + "?includeLand=true"
        req = requests.get(url, headers=requestHeaders)
        image_data = req.content
        image_file = BytesIO(image_data)
        image = Image.open(image_file)
        array = np.array(image) 
        (time, run) = fileId[27:].split("_+")
        # Convert timestamp string to datetime object
        timestamp = datetime.strptime(latestRunDateTime, '%Y-%m-%dT%H:%M:%SZ')
        # Add hours to the datetime object
        timestamp += timedelta(hours=int(time))

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(latestRunDateTime + "_" + time)

        blob.upload_from_string(image_data, content_type='image/png')
        print('Wrote', fileId)


def upload_latest_run_files(request):
    latestRunDateTime = get_latest_runtime()
    upload_files(latestRunDateTime)
    return('complete')
