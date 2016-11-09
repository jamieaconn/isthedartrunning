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
from time import gmtime, strftime, strptime, mktime
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


testing = True

if (testing):
    err_print = 1 # st to 1 for lots of printing messages : )
    image = 'test.png'
    database = 'test.db'
    os.system("cp data.db test.db")
    cur_time = strftime("%Y-%m-%dT%H:%M", gmtime())
    image_name = "testing/" + cur_time + ".png"
else:
    err_print = 0 # st to 1 for lots of printing messages : )
    image = 'graph.png'
    database = 'data.db'
    cur_time = strftime("%Y-%m-%dT%H:%M", gmtime())
    image_name = "forecast/" + cur_time + ".png"

river = 'nevis'
time_format = "%Y-%m-%dT%H:%M"

k = 0.26
scale_m = 2.099 
scale_a = 0.375
delay = 4

def f(x):
    return math.exp(k*x)
def g(x):
    return (scale_m * x) + scale_a
def f_inv(x):
    return math.log(x) / k
def g_inv(x):
    return (x - scale_a) / scale_m



def interpolate(river):
    con = lite.connect(database)
    cur = con.cursor()
    # Returnes timestamp of last level update - we need to interpolate from here
    query = """
        SELECT timestamp, rain     
            from {river}
        WHERE 
            timestamp = (  
                SELECT MAX(timestamp) 
                    from {river}
                WHERE level IS NOT NULL)
        ORDER BY timestamp
    """
    cur.execute(query.format(river=river))
    last_level_update = cur.fetchall()

# Set interpolate to rain for all forecast images
    query = """
        UPDATE {river}
        SET interpolate = rain      
        WHERE 
            timestamp > (  
                SELECT MAX(timestamp) 
                    from {river}
                WHERE level IS NOT NULL)
    """
    cur.execute(query.format(river=river))


    # Returns timestamp and rain for all rain values past latest level update
    query = """
        SELECT timestamp, rain    
            from {river}
        WHERE 
            timestamp > (  
                SELECT MAX(timestamp) 
                    from {river}
                WHERE level IS NOT NULL)
            AND rain IS NOT NULL
        ORDER BY timestamp
    """
    cur.execute(query.format(river=river))


    rain_dict = cur.fetchall()
    data = last_level_update + rain_dict
    if (err_print == 1):
        print "DATA"
        print data
        print str(len(data))
    for x in range(0, len(data) - 1):
        beg_time = data[x][0]
        beg_rain = data[x][1]
        end_time = data[x + 1][0]
        end_rain = data[x + 1][1]
        beg_epoch = calendar.timegm(strptime(beg_time, time_format))        
        end_epoch = calendar.timegm(strptime(end_time, time_format))        
        
        diff = (end_epoch - beg_epoch) / 900
        rain_diff = end_rain - beg_rain
        if(err_print == 1):
            print "diff: " + str(diff)
            print str(rain_diff) 
            print beg_time
            print str(beg_rain) 
        for y in range(1, diff):
            time = strftime(time_format , gmtime(beg_epoch + (y * 900)))
            rain = beg_rain + y * (rain_diff / diff)
                     
            cur.execute("INSERT OR IGNORE INTO {river} (timestamp) VALUES('{time_val}')".format(river=river, time_val = time))
            cur.execute("UPDATE {river} SET interpolate=({rain_val}) WHERE timestamp = ('{time_val}')".format(river=river,rain_val = rain, time_val = time))
    

# NOW INTERPOLATE FORECAST RAINFALL
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
    if (err_print == 1):
        print data
        print str(len(data))
    for x in range(0, len(data) - 1):
        beg_time = data[x][0]
        beg_rain = data[x][1]
        end_time = data[x + 1][0]
        end_rain = data[x + 1][1]
        beg_epoch = calendar.timegm(strptime(beg_time, time_format))        
        end_epoch = calendar.timegm(strptime(end_time, time_format))        
        
        diff = (end_epoch - beg_epoch) / 900
        rain_diff = end_rain - beg_rain
        if(err_print == 1):
            print diff
            print str(rain_diff) 
            print beg_time
            print str(beg_rain) 
        for y in range(1, diff):
            time = strftime(time_format , gmtime(beg_epoch + (y * 900)))
            rain = beg_rain + y * (rain_diff / diff)
                     
            cur.execute("INSERT OR IGNORE INTO {river} (timestamp) VALUES('{time_val}')".format(river=river, time_val = time))
            cur.execute("UPDATE {river} SET interpolate=({rain_val}) WHERE timestamp = ('{time_val}')".format(river=river,rain_val = rain, time_val = time))
    
            #print time
            #print str(rain)
        if (err_print == 1):
            print end_time
            print str(end_rain)
 
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

    if (err_print == 1):
        print time_val

    time_val_delay = strptime(time_val, "%Y-%m-%dT%H:%M")
    time_val_delay =  strftime("%Y-%m-%dT%H:%M" ,gmtime(calendar.timegm(time_val_delay) - (delay * 60 * 15)))

    if (err_print == 1):
        print time_val_delay

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
    print rain
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
        if (err_print == 1):
            print "Using forecast rainfall"
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



def model(river):
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
    if (err_print == 1):
        print "Latest level update =: " + str(level_val)

    #back calculate the storage based on the that level and input that into the db. 
    storage_val = f_inv(g_inv(level_val))
    cur.execute("UPDATE {river} SET storage = ({storage_val}) WHERE timestamp = (SELECT MAX(timestamp) FROM {river} WHERE level IS NOT NULL)".format(river=river, storage_val = storage_val))

    if (err_print == 1):
        print "Inverse calculated storage =: " + str(storage_val)
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
    if (err_print == 1):
        print "Model iterations: " + str(nrow)

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
    if (err_print == 1):
        print "forecast iterations: " + str(f_nrow)

    #START FOR LOOP!
    for x in range(0, nrow + f_nrow):
        storage_val = bucket_iteration(cur, storage_val)
        if (storage_val == None):
            break
            print "something fucked up: storage is NULL"
    con.commit()
    con.close()
    return 1

def create_json(river, write_to_file = True):
    con = lite.connect(database)
    cur = con.cursor()

    query = """
        SELECT timestamp, rain, level, predict     
            from {river}
        ORDER BY timestamp DESC
        LIMIT 200
    """
    cur.execute(query.format(river=river))
    data  = cur.fetchall()

    levels = [[1000*mktime(strptime(n[0], time_format)), n[3]] for n in data]
    rain = [[n[1], n[3]] for n in data]        
    minValue =  min([n[0] for n in data])

    scaleX = {}
    series = {}
    series['values'] = levels
    series['rain'] = rain


    scaleX['minValue'] = 1000*mktime(strptime(minValue, time_format))
    output = {}
    output['type'] = 'line'
    output['scaleX'] = scaleX
    output['series'] = series
    print json.dumps(output, indent = 4)
    if write_to_file:
        with open('/var/www/html/nevis.json', 'w') as f:
            json.dump(output, f)

interpolate(river)
model(river)
create_json(river)



