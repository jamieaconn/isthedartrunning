#!/usr/bin/env python
from operator import itemgetter

import requests
import datetime
import numpy as np
from scipy import misc
import glob, os
import math
import urllib2
import urllib
import cStringIO
import calendar
from calendar import timegm
import csv
from time import gmtime, strftime, strptime, mktime
from tempfile import NamedTemporaryFile
import shutil
import requests
import json
import matplotlib
from numpy import recfromcsv
from subprocess import call
import ftplib
import sqlite3 as lite
import sys


from local_info import facebook_access 
database = 'data.db'


time_format = "%Y-%m-%dT%H:%M"

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


def pretty_print(data):
    for line in data:
        print "timestamp: " + str(line['timestamp']) + "     level: " + str(line['level']) + "      rain: " + str(line['rain']) + "        forecast: " + str(line['forecast']) + "       model_rain: " + str(line['model_rain'])

def pretty_print2(data):
    for line in data:
        print "timestamp: " + str(line['timestamp']) + "     level: " + str(line['level']) + "       model_rain: " + str(line['model_rain']) + "          storage: " + str(line['storage']) + "      prediction: " + str(line['predict'])
def get_data(river, limit):
    con = lite.connect(database)
    cur = con.cursor()

    query = """
        SELECT timestamp, rain, level, forecast 
            from {river}
        ORDER BY timestamp DESC
        LIMIT {limit}
    """
    cur.execute(query.format(river=river, limit=limit))
    result = cur.fetchall()

    data_list =  [{"timestamp" : line[0], "rain" : line[1], "level" : line[2], "forecast" : line[3]} for line in result]
    for line in data_list:
        line['model_rain'] = None
    return data_list

def add_missing_timestamps(data_list):
    min_timestamp = min([line['timestamp'] for line in data_list])
    max_timestamp = max([line['timestamp'] for line in data_list])
    min_epoch = calendar.timegm(strptime(min_timestamp, time_format))  
    max_epoch = calendar.timegm(strptime(max_timestamp, time_format))  
    epoch = min_epoch
    while epoch < max_epoch:
        epoch += 900
        timestamp = strftime(time_format, gmtime(epoch))
        if [line for line in data_list if line['timestamp'] == timestamp]:
            pass
        else:
            data_list.append({"timestamp" :timestamp, "level": None, "rain" : None, "forecast": None, "model_rain" : None})
    
    return sorted(data_list, key=itemgetter('timestamp'), reverse=True)

# REWRITE THIS ALL WITH PANDAS????!!!!
def calculate_rain(data_list):
    latest_rain_update = max([line for line in data_list if (line['rain'] is not None)], key=lambda x:x['timestamp'])
    first_rain_update = min([line for line in data_list if (line['rain'] is not None)], key=lambda x:x['timestamp'])
    dum = first_rain_update['rain']
    timestamps = [row['timestamp'] for row in data_list if (row['timestamp'] >= first_rain_update['timestamp']) & (row['timestamp'] <= latest_rain_update['timestamp'])]
    timestamps.reverse()
    for timestamp in timestamps:
        rain = [row['rain'] for row in data_list if row['timestamp'] == timestamp][0]
        if rain is None:
            model_rain = 0
        elif rain == dum:
            model_rain = 0
        elif rain < dum:
            dum = rain
            model_rain = rain
        elif rain > dum:
            model_rain = rain - dum
            dum = rain
        for row in data_list:
            if row['timestamp'] == timestamp:
                row.update({'model_rain' : model_rain})

    #Now Interpolate the forecast data using the last rain gauge datum too
    sub_list = [row for row in data_list if (row['timestamp'] > latest_rain_update['timestamp']) & (row['forecast'] is not None)] + [latest_rain_update]
    
    sub_list.reverse()
    for x in range(0, len(sub_list) - 1):
        beg_time = calendar.timegm(strptime(sub_list[x]['timestamp'], time_format)) 
        if x == 0:  
            beg_rain = sub_list[x]['model_rain']
            #print beg_rain
        else:
            beg_rain = sub_list[x]['forecast']
        #print "beg rain: " + str(beg_rain)
        end_time = calendar.timegm(strptime(sub_list[x+1]['timestamp'], time_format))
        end_rain = sub_list[x+1]['forecast']
        #print "end rain: " + str(end_rain)
        time_diff = (end_time - beg_time) / 900
        #print time_diff
        rain_diff = end_rain - beg_rain
        for y in range(0, time_diff + 1):
            time = strftime(time_format, gmtime(beg_time + (y * 900)))
            #print time
            rain = beg_rain + y * (rain_diff / time_diff)
            #print rain
            row = next((row for row in data_list if row['timestamp'] == time), None)
            #print row
            if row:
                for row in data_list:
                    if row['timestamp'] == time:
                        row['model_rain'] = rain
            else:
                data_list.append({
                            'level': None, 
                            'timestamp' : time,
                            'rain' : None,
                            'model_rain' : rain,
                            'forecast' : None
                            })
    data_list = sorted(data_list, key = itemgetter('timestamp'), reverse=True)
    return data_list



def model(data_list):
    data_list = [{'timestamp' : line['timestamp'], 'level' : line['level'], 'model_rain' : line['model_rain'] } for line in data_list]
    data_list.reverse() 

    
    latest_level_update =  max([line for line in data_list if (line['level']is not None)], key=lambda x:x['timestamp'])
    initial_storage = f_inv(g_inv(latest_level_update['level']))
    #print initial_storage
    for i in range(0, len(data_list)):
        if data_list[i]['timestamp'] == latest_level_update['timestamp']:
            data_list[i]['storage'] = initial_storage
            
            data_list[i]['predict'] = None
            storage = initial_storage
        if data_list[i]['timestamp'] > latest_level_update['timestamp']:
            rain = data_list[i - delay]['model_rain']
            predict = g(f(storage))
            storage = storage + rain - f(storage)
            data_list[i]['storage'] = storage
            data_list[i]['predict'] = predict
        else:
            data_list[i]['storage'] = None
            data_list[i]['predict'] = None
    data_list = sorted(data_list, key = itemgetter('timestamp'))
    return data_list


def gettime():
    time = gmtime(calendar.timegm(gmtime()))  #Current time 
    if(time[4] > 45): 
        timestamp = strftime("%Y-%m-%dT%H:45", time)
    elif(time[4] > 30):
        timestamp = strftime("%Y-%m-%dT%H:30", time)
    elif(time[4] > 15):
        timestamp = strftime("%Y-%m-%dT%H:15", time)
    else:
        timestamp = strftime("%Y-%m-%dT%H:00", time)
    return(timestamp)

def create_json(river, data):
    levels = [[1000*timegm(strptime(line['timestamp'], time_format)), line['level']] for line in data] 
    predict = [[1000*timegm(strptime(line['timestamp'], time_format)), line['predict']] for line in data] 
    rain = [[1000*timegm(strptime(line['timestamp'], time_format)), line['model_rain']] for line in data] 
    
    result = [{"timestamp" : 1000*timegm(strptime(line['timestamp'], time_format)), "rain" : line['model_rain'], "level" : line["level"], 'predict' : line['predict']} for line in data] 
    
    for line in result:
        if line['rain'] is not None:
            line['rain'] = round(line['rain'], 1)
        if line['predict'] is not None:
            line['predict'] = round(line['predict'], 3)
    
    current_time = gettime()
    current_row = [line for line in data if line['timestamp'] == current_time]
    current_epoch_ms = timegm(strptime(current_time, time_format)) * 1000 
    if current_row:
        if current_row[0]['level'] is not None: 
            current_level = current_row[0]['level']
        else:
            current_level = current_row[0]['predict']
    else:
        current_level = 0.123456789
        print "ERROR: Could not fetch level or predict at " + str(current_time)
    text = "NO"
    next_up = None

    if current_level >= 1.6:
        text = "THE DART IS MASSIVE"
    elif current_level >= 0.7:
        text = "YES"
    else:
        dum = [line['timestamp'] for line in data if (line['predict'] > 0.7) & (line['timestamp'] > current_time)]
        if dum:
            next_up = min(dum) 
            next_up = timegm(strptime(next_up, time_format)) * 1000
            if (next_up - current_epoch_ms) < 3600000:
                text = "THE DART WILL BE UP SHORTLY"


        

    output = {}       
    output['current_time'] = current_epoch_ms
    output['current_level'] = current_level 
    output['next_up'] = next_up
    output['text'] = text
    output['values'] = result
    
    #print json.dumps(output, indent =4)

    return output

def upload_json(testing, output, filename): 
    with open(filename, 'w') as f:
        json.dump(output, f)
    
    if testing:
        pass
    else:
        from local_info import ftp_url, ftp_pass, ftp_user, ftp_dir
        ftp = ftplib.FTP(ftp_url)
        ftp.login(ftp_user, ftp_pass)
        if ftp_dir is not None:
            ftp.cwd(ftp_dir)

        ext = os.path.splitext(filename)[1]
        if ext in (".txt", ".htm", ".html"):
            ftp.storlines("STOR " + filename, open(filename))
        else:
            ftp.storbinary("STOR " + filename, open(filename), 1024)


def post_facebook():
    r = requests.post("https://graph.facebook.com", data={'scrape': 'True', 'id' : '  http://isthedartrunning.co.uk/', 'access_token' : facebook_access})


    #print(r.status_code, r.reason)
    #print(r.text[:300] + '...')


def run_model(testing=False):
    river = "dart"
    limit = 200

    data = get_data(river, limit)

    data = add_missing_timestamps(data)


    data = calculate_rain(data)

    #pretty_print(data)



    data = model(data)

    #pretty_print2(data)

    output = create_json(river, data)


    upload_json(testing, output, river + '.json')
    
    post_facebook()

def main():
    run_model(True)

if __name__ == "__main__":
    main()


#test
