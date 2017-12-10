import json
import requests
from time import gmtime, strftime, strptime
import calendar
from scipy.misc import imread
from io import BytesIO


from local_info import metoffice_key


"""
TODO
1. Add some logging and error catching
2. Rewrite the time/calendar bits
3. Add imread(BytesIO(r.content)) for the array stuff
"""

def get_radar_times():
    print "Requesting radar times"
    radar_times_url = 'http://datapoint.metoffice.gov.uk/public/data/layer/wxobs/all/json/capabilities'
    try:
        r = requests.get(radar_times_url, params={"key" : metoffice_key})
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print err
        sys.exit(1)

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
        sys.exit(1)

    with open('../image/radar/' + timestamp + '.png', "wb") as ff:
        ff.write(r.content)
    return misc.imread(BytesIO(r.content))

def time_fct(model_time, step): # Takes the model timestamp and adds the number of hours to get the timestamp for the image forecast
    # Turns string into UTC_struct
    time= strptime(model_time, "%Y-%m-%dT%H:%M")
    # Turns UTC_struct into seconds since epoch adds on a multiple of hours and then returns to UTC-Struct and then string!
    return strftime("%Y-%m-%dT%H:%M" ,gmtime(calendar.timegm(time) + (3600 * step)))


def get_forecast_radar_times():
    print "Requesting forecast radar times"
    forecast_radar_times_url = 'http://datapoint.metoffice.gov.uk/public/data/layer/wxfcs/all/json/capabilities'
    try:
        r = requests.get(forecast_radar_times_url, params={"key" : metoffice_key})
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print err
        sys.exit(1)
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
    #timestamp = time_fct(model_timestamp, step)
    forecast_radar_url = "http://datapoint.metoffice.gov.uk/public/data//layer/wxfcs/Precipitation_Rate/png"
    print "Requesting radar for", model_timestamp + "_" + str(step)

    try:
        r = requests.get(forecast_radar_url, params={"key" : metoffice_key, "RUN":model_timestamp+":00Z", "FORECAST":step})
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print err
        sys.exit(1)
    

    filename = model_timestamp + "_" + str(step) + ".png"
    with open('../image/forecast/' + filename, "wb") as ff:
        ff.write(r.content)
    return misc.imread(BytesIO(r.content))



"""THESE FUNCTIONS SHOULD SLOT INTO THE OTHER CODE SOMEWHERE"""

def get_radar_images():
    timestamps = get_radar_times()
    for timestamp in timestamps:
        get_radar_image(timestamp)

def get_forecast_radar_images():
    model_timestamp, steps = get_forecast_radar_times()
    for step in steps:
        get_forecast_radar_image(model_timestamp, step)
        


