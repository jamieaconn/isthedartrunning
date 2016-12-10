#!/usr/bin/env python

import numpy as np
from scipy import misc
import glob, os
import urllib2
import urllib
import cStringIO
import calendar
import csv
from time import gmtime, strptime,  strftime
from tempfile import NamedTemporaryFile
import shutil
import requests
import json
from numpy import recfromcsv
from subprocess import call
import ftplib
import sqlite3 as lite
import sys
import os.path

fdir = os.path.abspath(os.path.dirname(__file__))




database = os.path.join(fdir, 'data.db')

rivers = ['dart', 'nevis']
bounds = {
    'dart': {'Nmin' : 396, 'Nmax' : 408, 'Emin':230, 'Emax':242},
    'nevis': {'Nmin' : 162, 'Nmax' : 164, 'Emin':205, 'Emax':207}
}

white = np.array([199,191,193,128])
grey = np.array([0,0,0,0])
A = np.array([  0,   0, 254, 255])
B = np.array([ 50, 101, 254, 255])
C = np.array([127, 127,   0, 255])
D = np.array([254, 203,   0, 255])
E = np.array([254, 152,   0, 255])
F = np.array([254,   0,   0, 255])
G = np.array([254,   0, 254, 255])

def update_sql(river, time_val, forecast_val):
    con = lite.connect(database)
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO {river} (timestamp) VALUES('{time_val}')".format(river=river,time_val = time_val))
    cur.execute("UPDATE {river} SET forecast=({forecast_val}) WHERE timestamp = ('{time_val}')".format(river=river, forecast_val = forecast_val, time_val = time_val))
    con.commit()
    con.close()


def time_fct(model_time, step): # Takes the model timestamp and adds the number of hours to get the timestamp for the image forecast
    # Turns string into UTC_struct
    time= strptime(model_time, "%Y-%m-%dT%H:%M")
    # Turns UTC_struct into seconds since epoch adds on a multiple of hours and then returns to UTC-Struct and then string!
    return strftime("%Y-%m-%dT%H:%M" ,gmtime(calendar.timegm(time) + (3600 * step)))


def png(river, model_time, hour, timestamp): #gets image from metoffice and returns the rain in the dart catchment

    os.chdir(os.path.join(fdir, "image/forecast"))
    if (hour < 10):
        url = "http://datapoint.metoffice.gov.uk//public//data//layer//wxfcs//Precipitation_Rate//png?RUN=" + model_time + ":00Z&FORECAST=" + str(hour) + "&key=78e077ee-7ec6-408c-9b04-b23480cbb589"
    else: 
        url = "http://datapoint.metoffice.gov.uk//public//data//layer//wxfcs//Precipitation_Rate//png?RUN=" + model_time + ":00Z&FORECAST=" + str(hour) + "&key=78e077ee-7ec6-408c-9b04-b23480cbb589"

    #print url
    urllib.urlretrieve(url, timestamp + ".png")
    file = cStringIO.StringIO(urllib2.urlopen(url).read())
    b = misc.imread(file)
    rain = 0
    for i in range(bounds[river]['Nmin'], bounds[river]['Nmax'] ):
        for j in range(bounds[river]['Emin'], bounds[river]['Emax']):
            if((b[i,j]==white).all() == True):
                pass
            elif((b[i,j]==grey).all() == True):
                pass
            elif((b[i,j]== A).all() == True):
                rain = rain + 0.3    
            elif((b[i,j]== B).all() == True):
                rain = rain + 0.75
                
            elif((b[i,j]== C).all() == True):
                rain = rain + 1.5
                
            elif((b[i,j]== D).all() == True):
                rain = rain + 3
                
            elif((b[i,j]== E).all() == True):
                rain = rain + 6
                
            elif((b[i,j]== F).all() == True):
                rain = rain + 12
                
            elif((b[i,j]== G).all() == True):
                rain = rain + 24
                
            else:
                rain = rain + 32
    os.chdir("..")
    os.chdir("..")
    pixels = (bounds[river]['Nmax'] - bounds[river]['Nmin']) * (bounds[river]['Emax'] - bounds[river]['Emin'])
    return(rain/(pixels)) 


def update_forecast_rainfall(testing):
    metoff = 'http://datapoint.metoffice.gov.uk/public/data/layer/wxfcs/all/json/capabilities?key=78e077ee-7ec6-408c-9b04-b23480cbb589'
    response = urllib2.urlopen(metoff)
    data = json.load(response)

    # ret=rns the most recent model run timestamp
    model_time = data["Layers"]["Layer"][0]["Service"]["Timesteps"]["@defaultTime"]
    #Remove last bit of the timestamp
    model_time = model_time[:16]

    #returns all of the images available as hours since the model rain
    timesteps =  data["Layers"]["Layer"][0]["Service"]["Timesteps"]["Timestep"]
    #print model_time
    for step in timesteps:
        #print step
        timestamp = time_fct(model_time, step)
        for river in rivers:
            #print timestamp
            rain = png(river, model_time, step, timestamp)
            #print rain
            update_sql(river, timestamp, rain)

def main():
    update_forecast_rainfall(False)
if __name__ == "__main__":
    main()

