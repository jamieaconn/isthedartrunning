import json
import requests
from time import gmtime, strftime, strptime
import calendar
from scipy import misc
from io import BytesIO
import os

from local_info import metoffice_key

fdir = os.path.dirname(__file__)

img_dirs = {
    "radar_img_dir": os.path.abspath(os.path.join(fdir, "../image/radar")),
    "forecast_img_dir": os.path.abspath(os.path.join(fdir, "../image/forecast")),
}

for key in img_dirs.keys():
    if not os.path.exists(img_dirs[key]):
        os.makedirs(img_dirs[key])

"""
TODO
1. Add some logging and error catching
2. Rewrite the time/calendar bits
"""

def get_radar_times():
    print "Requesting radar times"
    radar_times_url = 'http://datapoint.metoffice.gov.uk/public/data/layer/wxobs/all/json/capabilities'
    try:
        r = requests.get(radar_times_url, params={"key" : metoffice_key})
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print err


    data = json.loads(r.content)
    timestamps = [lay for lay in data['Layers']['Layer'] if lay['@displayName'] == 'Rainfall'][0]['Service']['Times']['Time']
    return timestamps

def get_radar_image(timestamp):
    """Request radar image from metoffice and save to disk and return as array"""
    radar_url = "http://datapoint.metoffice.gov.uk/public/data/layer/wxobs/RADAR_UK_Composite_Highres/png"
    print "Requesting radar for", timestamp
    try:
        r = requests.get(radar_url, params={"TIME" : timestamp + "Z", "key": metoffice_key})
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print err

    with open(os.path.join(img_dirs["radar_img_dir"], timestamp + '.png'), "wb") as ff:
        ff.write(r.content)
    return misc.imread(BytesIO(r.content))

def get_forecast_radar_times():
    print "Requesting forecast radar times"
    forecast_radar_times_url = 'http://datapoint.metoffice.gov.uk/public/data/layer/wxfcs/all/json/capabilities'
    try:
        r = requests.get(forecast_radar_times_url, params={"key" : metoffice_key})
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print err

    data = json.loads(r.content)

    # time when the model ran (remove last three characters from string)
    model_timestamp = data["Layers"]["Layer"][0]["Service"]["Timesteps"]["@defaultTime"][:16]
    print
    print "Radar images for model run at", model_timestamp
    print
    #returns all of the timesteps available as hours since the model rain
    steps =  data["Layers"]["Layer"][0]["Service"]["Timesteps"]["Timestep"]
    return model_timestamp, steps


def get_forecast_radar_image(model_timestamp, step):
    """Request forecast radar image from metoffice, save to disk and return as array"""
    forecast_radar_url = "http://datapoint.metoffice.gov.uk/public/data//layer/wxfcs/Precipitation_Rate/png"
    print "Requesting radar for", model_timestamp + "_" + str(step)

    try:
        r = requests.get(forecast_radar_url, params={"key" : metoffice_key, "RUN":model_timestamp+":00Z", "FORECAST":step})
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print err

    

    filename = model_timestamp + "_" + str(step) + ".png"
    with open(os.path.join(img_dirs["forecast_img_dir"], filename), "wb") as ff:
        ff.write(r.content)
    return misc.imread(BytesIO(r.content))
