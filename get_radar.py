#!/usr/bin/env python


import datetime
import numpy as np
from scipy import misc
import glob, os
import math
import urllib2
import urllib
import cStringIO
import calendar
import csv
from time import gmtime, strftime, strptime
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

river = 'dart'
database = os.path.join(fdir, 'data.db')

def gettime():
    time = gmtime(calendar.timegm(gmtime()) - 960)  #Current time - 16 minutes
    if(time[4] > 45): 
        timestamp = strftime("%Y-%m-%dT%H:45", time)
    elif(time[4] > 30):
        timestamp = strftime("%Y-%m-%dT%H:30", time)
    elif(time[4] > 15):
        timestamp = strftime("%Y-%m-%dT%H:15", time)
    else:
        timestamp = strftime("%Y-%m-%dT%H:00", time)
    return(timestamp)


def get_png(): #gets image from metoffice and returns the rain in the dart catchment
    timestamp = gettime()
    url = "http://datapoint.metoffice.gov.uk//public//data//layer//wxobs//RADAR_UK_Composite_Highres//png?TIME=" + timestamp + ":00Z&key=78e077ee-7ec6-408c-9b04-b23480cbb589"


    urllib.urlretrieve(url,  '/home/ubuntu/testing/isthedartrunning/image/radar/' + timestamp + ".png")


# Get's current time - 16 minutes and rounded down to 15 minute interval
#timestamp = gettime()
#updates sql with all level update for previous and current day
def main():
    get_png()
if __name__ == "__main__":
    main()
# gets latest radar image and returns rain from dart catchment
#rain = png(timestamp)
#interpolates forecast data. Could this be in forecast.py?
#interpolate()
#Runs the model to create the predictions! Updates sql
#model()
# Tkaes sql data and creates plot. FTP connects to website and updates with image.
#sql_plot(timestamp)

