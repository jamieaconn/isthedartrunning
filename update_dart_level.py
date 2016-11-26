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

river = 'dart'
database = 'data.db'

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

def upload(ftp, file):
    ext = os.path.splitext(file)[1]
    if ext in (".txt", ".htm", ".html"):
        ftp.storlines("STOR " + file, open(file))
    else:
        ftp.storbinary("STOR " + file, open(file, "rb"), 1024)

def png(timestamp): #gets image from metoffice and returns the rain in the dart catchment
    white = np.array([199,191,193,128])
    grey = np.array([0,0,0,0])
    A = np.array([  0,   0, 254, 255])
    B = np.array([ 50, 101, 254, 255])
    C = np.array([127, 127,   0, 255])
    D = np.array([254, 203,   0, 255])
    E = np.array([254, 152,   0, 255])
    F = np.array([254,   0,   0, 255])
    G = np.array([254,   0, 254, 255])

    os.chdir("image")
    url = "http://datapoint.metoffice.gov.uk//public//data//layer//wxobs//RADAR_UK_Composite_Highres//png?TIME=" + timestamp + ":00Z&key=78e077ee-7ec6-408c-9b04-b23480cbb589"


    urllib.urlretrieve(url, timestamp + ".png")
    file = cStringIO.StringIO(urllib2.urlopen(url).read())
    b = misc.imread(file)
    rain = 0
    for i in range(400, 404):
        for j in range(234, 238):
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
    pixels = 4*4
    return(rain/(pixels * 4)) #remember that this is rain rate and time period is 15 mintues so we need to / 4


# Get's current time - 16 minutes and rounded down to 15 minute interval
#timestamp = gettime()
#updates sql with all level update for previous and current day
def main():
    level(testing) 


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

