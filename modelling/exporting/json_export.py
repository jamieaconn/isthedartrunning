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
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from numpy import recfromcsv
from subprocess import call
import ftplib
import sqlite3 as lite
import sys

database = 'data.db'
plot_range = 300


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

timestamp = gettime()
con = lite.connect(database)
cur = con.cursor()
query = """
    SELECT timestamp, predict
    FROM (
    SELECT * 
    FROM 
        dart
    WHERE predict IS NOT NULL OR level IS NOT NULL
    ORDER BY timestamp DESC
    LIMIT ?) 

    ORDER BY
    timestamp ASC

"""
cur.execute(query, (plot_range, ))
data =  cur.fetchall()
con.commit()       
con.close()

json_string = json.dumps(dict(data))

with open('json.txt', 'w') as outfile:
    json.dump(dict(data), outfile)



