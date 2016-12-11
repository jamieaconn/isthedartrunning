
# coding: utf-8

# # NICE STATS

# In[2]:

import sqlite3 as lite
import math
import time
import sys
import json
import pandas as pd
import os
import ftplib
import numpy as np

fdir = os.path.abspath(os.path.dirname('__file__'))
start_time = time.time()



# In[57]:

# Set to True to use a nice sample db
sample_data = False

# set to True for printed messages
verbose = True

river = 'dart'
# In[58]:

time_format = "%Y-%m-%dT%H:%M"

if sample_data:
    database = os.path.join(fdir, 'sample_data.db')
else:
    database = os.path.join(fdir, 'data.db')



# In[59]:

# Get current time rounded down to nearest 15 minutes
current_time = time.time()
current_time = current_time - (current_time % (15*60))
current_time = pd.to_datetime(current_time, unit='s')

if sample_data:
    current_time = pd.to_datetime('2016-11-21 18:30:00') 
if verbose:
    print current_time


con = lite.connect(database)
cur = con.cursor()
query = """
        SELECT timestamp, rain, level, forecast 
            from {river}
        ORDER BY timestamp DESC
    """
cur.execute(query.format(river=river))
result = cur.fetchall()

df_all = pd.DataFrame(result, columns=['timestamp', 'cum_rain', 'level', 'forecast'])

df_all.head()


# In[61]:

df_all.timestamp = pd.to_datetime(df_all.timestamp)
df_all = df_all.set_index('timestamp')
df_all = df_all.sort_index()

df_all.head(10)


# In[ ]:




# In[63]:

# LAST TIME THAT THE DART RAN
up_rows = df_all[df_all.level > 0.7].index
last_up = None
if len(up_rows) > 0:
    last_up = pd.to_datetime(max(up_rows))
if verbose:
    print 'current_time: ' + str(current_time)

if last_up:
    if verbose:
        print 'last_up: ' + str(last_up)

    diff = (current_time - last_up)

    last_up_days = diff.value / (24 * 60 * 60 * 1000 * 1000 * 1000)
    last_up_text = str(last_up_days) + ' DAYS'
    if last_up_days == 0:
        last_up_hours = diff.value / (60 * 60 * 1000 * 1000 * 1000)
        last_up_text = str(last_up_hours) + ' HOURS'
        if last_up_hours == 0:
            last_up_minutes = diff.value / (60 * 1000 * 1000 * 1000)
            last_up_text = str(last_up_minutes) + ' MINUTES'
    if verbose:
        print
        print 'LAST RUNNING ' + last_up_text + ' AGO'
else:
    last_up_text = "NEVER?!"
    if verbose:
        print last_up_text


# In[90]:

# NUMBER OF DAYS THAT THE DART HAS RUN IN DATA
df_days = df_all.resample('D').max()
#print len(df_days[df_days.level > 0.7])


# NUMBER OF DAYS THAT THE DART HAS RUN IN LAST WEEK
df_last_week = df_days[(current_time - df_days.index) < np.timedelta64(7,'D')]
days_up_week = len(df_last_week[df_last_week.level > 0.7])
max_level_week = df_last_week.level.max().round(2)

if verbose:
    print 'UP ON ' + str(days_up_week) + ' DAYS IN THE LAST 7 DAYS'
    print 'HIGHEST LEVEL IN THE LAST 7 DAYS WAS ' + str(max_level_week)

# NUMBER OF DAYS THAT DART HAS RUN IN LAST MONTH
df_last_month = df_days[(current_time - df_days.index) < np.timedelta64(30,'D')]
days_up_month = len(df_last_month[df_last_month.level > 0.7])
max_level_month = df_last_month.level.max().round(2)

if verbose:
    print 'UP ON ' + str(days_up_month) + ' DAYS IN THE LAST 30 DAYS'
    print 'HIGHEST LEVEL IN THE LAST 30 DAYS WAS ' + str(max_level_month)




# In[91]:

# SUM OF RAIN IN THE LAST 24 HOURS ... 
# ...A bit more tricky, use cum_rain and somehow take out the max from previous day and today and sum 

# SUM OF RAIN IN THE LAST WEEK
sum_rain_week = int(round(sum(df_last_week.cum_rain.fillna(0))))

sum_rain_month = int(round(sum(df_last_month.cum_rain.fillna(0))))


# SUM OF RAIN IN THE LAST MONTH
if verbose:
    print str(sum_rain_week) + ' MM OF RAIN IN THE LAST 7 DAYS'
    print str(sum_rain_month) + ' MM OF RAIN IN THE LAST 30 DAYS'


# In[94]:

data = {}       
data['current_time'] = current_time.value / 1000000
data['last_up_text'] = last_up_text
data['days_up_week'] = days_up_week
data['max_level_week'] = max_level_week.round(2)
data['days_up_month'] = days_up_month
data['max_level_month'] = max_level_month
data['sum_rain_week'] = sum_rain_week
data['sum_rain_month'] = sum_rain_month


filename = os.path.join(fdir, 'dart_stats.json')
with open(filename, 'w') as f:
    json.dump(data, f, indent=4)


