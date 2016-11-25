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

forecast = False
river = 'nevis'
rain_url = 'http://beta.sepa.org.uk/rainfall/api/Hourly/115343'
level_url = 'http://apps.sepa.org.uk/database/riverlevels/116011-SG.csv'
database = 'data.db'

plot_range = 300
k = 0.12
scale_m = 1.91 
scale_a = 0.234
delay = 4

def f(x):
    return math.exp(k*x)
def g(x):
    return (scale_m * x) + scale_a
def f_inv(x):
    return math.log(x) / k
def g_inv(x):
    return (x - scale_a) / scale_m


def rain_and_level(testing=False):
    # UPDATES DB WITH LATEST LEVELS AND RAINFALL

    # Get csv for level for the last 24 hours
    # For each row timestamp to SQL db unless already exists in which case update

    # Get json for rain data for last 24 hours

    r = requests.get(rain_url)
    if(r.status_code != 200):
        print "level json request failed"
    else:
        data = r.json()
        #print json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
        con = lite.connect(database)
        cur = con.cursor()
        for x in range(0, len(data)):    
            time =  data[x]['Timestamp']
            value =  data[x]['Value']
            #Convert timestamp to standardised format
            time = strptime(time[:16], "%d/%m/%Y %H:%M")
            time =  strftime("%Y-%m-%dT%H:%M", time)
            cur.execute("INSERT OR IGNORE INTO nevis (timestamp) VALUES('{time_val}')".format(time_val = time))
            cur.execute("UPDATE nevis SET rain=({rain_val}) WHERE timestamp = ('{time_val}')".format(rain_val = value,time_val = time))
        
    # For each timestamp add to SWL unless already exists in which case update

    try:
        response = urllib2.urlopen(level_url)
    except:
        if testing:
            print "Failed to access Level CSV: " + level_url
        return
    data = csv.reader(response)

    for row in data:
        time =  row[0]
        value = row[1]
        
        try: 
            time = strptime(time[:16], "%d/%m/%Y %H:%M")    
            time =  strftime("%Y-%m-%dT%H:%M", time)
            cur.execute("INSERT OR IGNORE INTO nevis (timestamp) VALUES('{time_val}')".format(time_val = time))
            cur.execute("UPDATE nevis SET level=({level_val}) WHERE timestamp = ('{time_val}')".format(level_val = value,time_val = time))
        except ValueError:
            pass


    query = """
        UPDATE {river} 
        SET rain = 0
        WHERE rain IS NULL

    """
    cur.execute(query.format(river=river))
    con.commit()
    con.close()


def interpolate():
    con = lite.connect(database)
    cur = con.cursor()
    
    # Returns timestamp and rain of latest radar image    
    query = """
        SELECT timestamp, rain     
            from {river}
        WHERE 
            timestamp = (  
                SELECT MAX(timestamp) 
                    from {river}
                WHERE rain IS NOT NULL)
        ORDER BY timestamp
    """
    cur.execute(query.format(river=river))
    latest_rain = cur.fetchall()
    

# Set interpolate to forecast for all forecast images
    query = """
        UPDATE {river}
        SET interpolate = forecast      
        WHERE 
            timestamp > (  
                SELECT MAX(timestamp) 
                    from {river}
                WHERE rain IS NOT NULL)
            AND forecast IS NOT NULL
    """
    cur.execute(query.format(river=river))
    

    # Returns timestamp and rain for all forecast images
    query = """
        SELECT timestamp, forecast      
            from {river}
        WHERE 
            timestamp > (  
                SELECT MAX(timestamp) 
                    from {river}
                WHERE rain IS NOT NULL)
            AND forecast IS NOT NULL
        ORDER BY timestamp
    """
    cur.execute(query.format(river=river))


    forecast_rain = cur.fetchall()
    data = latest_rain + forecast_rain
    for x in range(0, len(data) - 1):
        beg_time = data[x][0]
        beg_rain = data[x][1]
        end_time = data[x + 1][0]
        end_rain = data[x + 1][1]
        beg_epoch = calendar.timegm(strptime(beg_time, "%Y-%m-%dT%H:%M"))        
        end_epoch = calendar.timegm(strptime(end_time, "%Y-%m-%dT%H:%M"))        
        
        diff = (end_epoch - beg_epoch) / 900
        rain_diff = end_rain - beg_rain
        for y in range(1, diff):
            time = strftime("%Y-%m-%dT%H:%M" , gmtime(beg_epoch + (y * 900)))
            rain = beg_rain + y * (rain_diff / diff)
                     
            cur.execute("INSERT OR IGNORE INTO {river} (timestamp) VALUES('{time_val}')".format(river=river, time_val = time))
            cur.execute("UPDATE {river} SET interpolate=({rain_val}) WHERE timestamp = ('{time_val}')".format(river=river,rain_val = rain, time_val = time))
    
            #print time
            #print str(rain)
 
    con.commit()
    con.close()


def level():

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

# FROM all timesteps greater than the one with the last level update, take the min timestamp that has NULL in predict

def bucket_iteration(cur, storage_val):
    query = """

        SELECT MIN(timestamp) 
        FROM {river} 
        WHERE 
        timestamp > (SELECT MAX(timestamp) FROM {river} WHERE level IS NOT NULL) AND predict IS NULL
    """

    cur.execute(query.format(river=river))

    time_val = cur.fetchall()
    time_val = time_val[0][0]


    time_val_delay = strptime(time_val, "%Y-%m-%dT%H:%M")
    time_val_delay =  strftime("%Y-%m-%dT%H:%M" ,gmtime(calendar.timegm(time_val_delay) - (delay * 60 * 15)))


    query = """
        SELECT 
        rain 
        FROM 
        {river} 
        WHERE 
        timestamp = '{time_val_delay}'
    """
    cur.execute(query.format(river=river, time_val_delay = str(time_val_delay) ))

    rain = cur.fetchall()
    if (rain[0][0] == None):        
        query = """
            SELECT 
            interpolate 
            FROM 
            {river} 
            WHERE 
            timestamp = '{time_val_delay}'
        """
        cur.execute(query.format(river=river, time_val_delay=time_val_delay ))

        rain = cur.fetchall()
        if (rain[0][0] == None):
            print "Couldn't fetch rain from " + database
            return None
    rain = rain[0][0]

    predict_val = g(f(storage_val))
    storage_val = storage_val + rain - f(storage_val)

    query = """
        UPDATE 
        {river} 
        SET 
        predict = {predict_val}, storage = {storage_val}
        WHERE 
        timestamp = '{time_val}'

    """
    cur.execute(query.format(river=river, predict_val=predict_val, storage_val=storage_val, time_val=time_val))
    return storage_val



def model():
    con = lite.connect(database)
    cur = con.cursor()

    #set predict to level for timestamp <= latest level reading
    cur.execute("UPDATE {river} SET predict = level WHERE timestamp <= (SELECT MAX(timestamp) FROM {river} WHERE level IS NOT NULL)".format(river=river))

    #Set all predicts to NULL for timestamps > latest level reading
    cur.execute("UPDATE {river} SET predict = NULL WHERE timestamp > (SELECT MAX(timestamp) FROM {river} WHERE level IS NOT NULL)".format(river=river))

    #return value of level at last update
    cur.execute("SELECT level FROM {river} WHERE timestamp = (SELECT MAX(timestamp) FROM {river} WHERE level IS NOT NULL)".format(river=river))
    all_rows = cur.fetchall()
    level_val =  all_rows[0][0]

    #back calculate the storage based on the that level and input that into the db. 
    storage_val = f_inv(g_inv(level_val))
    cur.execute("UPDATE {river} SET storage = ({storage_val}) WHERE timestamp = (SELECT MAX(timestamp) FROM {river} WHERE level IS NOT NULL)".format(river=river, storage_val = storage_val))

    #FIND HOW MANY ROWS
    query = """

        SELECT count(*) 
        FROM {river}
        WHERE 
        timestamp > (SELECT MAX(timestamp) FROM {river} WHERE level IS NOT NULL) AND predict IS NULL AND
        rain IS NOT NULL
    """
    cur.execute(query.format(river=river))

    nrow = cur.fetchall()
    nrow = nrow[0][0] 

    #FIND HOW MANY  forecast ROWS
    query = """

        SELECT count(*) 
        FROM {river} 
        WHERE 
        timestamp > (SELECT MAX(timestamp) FROM {river} WHERE rain IS NOT NULL) AND interpolate IS NOT NULL
    """
    cur.execute(query.format(river=river))

    f_nrow = cur.fetchall()
    f_nrow = f_nrow[0][0] 

    #START FOR LOOP!
    for x in range(0, nrow + f_nrow):
        storage_val = bucket_iteration(cur, storage_val)
        if (storage_val == None):
            break
            print "something fucked up: storage is NULL"
    con.commit()
    con.close()
    return 1




def forecast_update_sql(time_val, forecast_val):
    con = lite.connect('data.db')
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO {river} (timestamp) VALUES('{time_val}')".format(river=river, time_val = time_val))
    cur.execute("UPDATE {river} SET forecast=({forecast_val}) WHERE timestamp = ('{time_val}')".format(river=river, forecast_val = forecast_val, time_val = time_val))
    con.commit()
    con.close()


def time_fct(model_time, step): # Takes the model timestamp and adds the number of hours to get the timestamp for the image forecast
    # Turns string into UTC_struct
    time= strptime(model_time, "%Y-%m-%dT%H:%M")
    # Turns UTC_struct into seconds since epoch adds on a multiple of hours and then returns to UTC-Struct and then string!
    return strftime("%Y-%m-%dT%H:%M" ,gmtime(calendar.timegm(time) + (3600 * step)))


def main():
    rain_and_level()

if __name__ == "__main__":
    main()
#Update database with newest rain values and river levels
#interpolates forecast data. Could this be in forecast.py?
#interpolate()
#Runs the model to create the predictions! Updates sql
#model()


