import datetime
import numpy as np
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

from scipy import sum, average, misc
fdir = os.path.abspath(os.path.dirname(__file__))


import dartcom

import scrapeRadar

river = 'dart'
database = os.path.join(fdir, '../data.db')

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



def update_sql_rain(time_val, rain_val):
    con = lite.connect(database)
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO {river} (timestamp) VALUES('{time_val}')".format(river=river, time_val = time_val))
    cur.execute("UPDATE {river} SET rain=({rain_val}) WHERE timestamp = ('{time_val}')".format(river=river, rain_val = rain_val, time_val = time_val))
    con.commit()
    con.close()


def update_sql(river, time_val, forecast_val):
    con = lite.connect(database)
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO {river} (timestamp) VALUES('{time_val}')".format(river=river,time_val = time_val))
    cur.execute("UPDATE {river} SET forecast=({forecast_val}) WHERE timestamp = ('{time_val}')".format(river=river, forecast_val = forecast_val, time_val = time_val))
    con.commit()
    con.close()


def upload(ftp, file):
    ext = os.path.splitext(file)[1]
    if ext in (".txt", ".htm", ".html"):
        ftp.storlines("STOR " + file, open(file))
    else:
        ftp.storbinary("STOR " + file, open(file, "rb"), 1024)

def time_fct(model_time, step): # Takes the model timestamp and adds the number of hours to get the timestamp for the image forecast
    # Turns string into UTC_struct
    time= strptime(model_time, "%Y-%m-%dT%H:%M")
    # Turns UTC_struct into seconds since epoch adds on a multiple of hours and then returns to UTC-Struct and then string!
    return strftime("%Y-%m-%dT%H:%M" ,gmtime(calendar.timegm(time) + (3600 * step)))


def rain_from_radar(image, river):
    b = image
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
    pixels = (bounds[river]['Nmax'] - bounds[river]['Nmin']) * (bounds[river]['Emax'] - bounds[river]['Emin'])
    return(rain/(pixels)) 


def update_forecast_rainfall(testing):
    model_timestamp, steps = get_forecast_radar_times()

    for step in steps:
        timestamp = time_fct(model_timestamp, step)
        image = scrapeRadar.get_forecast_radar_image(model_timestamp, step)

        for river in rivers:
            #print timestamp
            rain = rain_from_radar(image, river)
            #print rain
            update_sql(river, timestamp, rain)


def level(testing=False):

    end_date = strftime("%Y-%m-%d", gmtime())
    start_date =  strftime("%Y-%m-%d", gmtime(calendar.timegm(gmtime()) - 86400))  
    
    url = 'http://environment.data.gov.uk/flood-monitoring/id/stations/46126/readings?startdate=' + start_date + '&enddate=' + end_date + '&_sorted'
    r = requests.get(url)
    if(r.status_code != 200):
        print "level json request failed"
        return 0
    else:
        con = lite.connect(database)
        cur = con.cursor()
        data = r.json()
        for x in range(0, len(data['items'])):
            time = data['items'][x]['dateTime']
            time = time[:16]
            value = data['items'][x]['value']
            cur.execute("INSERT OR IGNORE INTO {river} (timestamp) VALUES('{time_val}')".format(river=river,time_val = time))
            cur.execute("UPDATE {river} SET level=({level_val}), predict=({predict_val}) WHERE timestamp = ('{time_val}')".format(river = river, level_val = value, predict_val = value, time_val = time))
        
        con.commit()
        con.close()



def sql_plot(timestamp):
    con = lite.connect(database)
    cur = con.cursor()
    query = """
        SELECT timestamp, predict
        FROM (
        SELECT * 
        FROM 
            {river}
        WHERE predict IS NOT NULL OR level IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT {plot_range}) 

        ORDER BY
        timestamp ASC

    """
    cur.execute(query.format(plot_range= plot_range, river=river ))
    data =  cur.fetchall()


    # get times as datetime object
    dates =[(datetime.datetime(*(strptime(r[0], "%Y-%m-%dT%H:%M")[0:6]))) for r in data]
    values = [r[1] for r in data]
    # PLOT THE PREDICT VALUES AGAINST TIME!!! NOT WORKING YET
    axes = plt.gca()
    axes.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    axes.set_ylim([0,2])

    #fig, ax = plt.subplots()
    #ax.plot_date(dates, values, 'b-')
    legend = "forecast updated at: UTC" + timestamp 
    plt.plot(dates, values, label = legend)
    plt.gcf().autofmt_xdate()
    plt.legend(loc = 'upper right')
    plt.savefig(image_name)

    ftp = ftplib.FTP("ftp.ipage.com")
    ftp.login('isthedartrunningcouk', 'iPage0123!')
    upload(ftp, image_name)
    con.commit()       
    con.close()


def gettime():
    time = gmtime()  #Current time - 16 minutes
    if(time[4] > 15 & time[4] < 45): 
        timestamp = strftime("%Y-%m-%dT%H:30", time)
    else:
        timestamp = strftime("%Y-%m-%dT%H:00", time)
    return(timestamp)


def rain(testing=False):

    timestamp = gettime()
    rain = dartcom.get_rainfall()

    #Update database with newest rain value
    update_sql_rain(timestamp, rain)
