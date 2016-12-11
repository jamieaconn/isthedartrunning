
# coding: utf-8

# In[101]:

import sqlite3 as lite
import math
import time
import sys
import json
import pandas as pd
import os
import ftplib
import numpy as np


start_time = time.time()



# In[102]:
verbose = True
sample_data = False
fdir = os.path.abspath(os.path.dirname(__file__))
# In[103]:

time_format = "%Y-%m-%dT%H:%M"


k = 0.12
scale_m = 1.91
scale_a = 0.234
delay = np.timedelta64(60, 'm') # 60 minutes

def f(x):
    return math.exp(k*x)
def g(x):
    return (scale_m * x) + scale_a
def f_inv(x):
    return math.log(x) / k
def g_inv(x):
    return (x - scale_a) / scale_m


# In[104]:

# Get current time rounded down to nearest 15 minutes
current_time = time.time()
current_time = current_time - (current_time % (15*60))
current_time = pd.to_datetime(current_time, unit='s')

if sample_data:
    current_time = pd.to_datetime('2016-11-21 18:30:00') 

if verbose:
    print 'current time: ' + str(current_time)


# # Load data from sql database into pandas df

# In[105]:

if sample_data:
    database = os.path.join(fdir, 'sample_data.db')
else:
    database = os.path.join(fdir,  '../data.db')
river = 'dart'
limit = 200
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
df = pd.DataFrame(result, columns=['timestamp', 'cum_rain', 'level', 'forecast'])


# In[ ]:




# # Set index to timestamp column as object

# In[106]:

df.timestamp = pd.to_datetime(df.timestamp)
df = df.set_index('timestamp')
df = df.sort_index()
#df.head()


# # Pre-model checks

# In[107]:


# Check that there is a level update in df
if len(df[df.level.notnull()]) == 0:
    print 'No level updates'
    sys.exit()   
# Check that there is a row for now or past now
if len(df[df.index >= current_time]) == 0:
    print 'Not enough data'
    sys.exit()

# In[108]:



# # Calculate important timestamps

# In[109]:

latest_level_time = max(df.index[df.level.notnull()])

latest_level = df.loc[latest_level_time].level


# In[110]:

latest_rain_time = max(df.index[df.cum_rain.notnull()])

if verbose:
    print 'latest level at: ' + str(latest_level_time)
    print 'latest level is: ' + str(latest_level)
    print 'latest rain update at: ' + str(latest_rain_time)


# # Fill in missing timestamps

# In[111]:

min_time = min(df.index)
max_time = max(df.index)
rng = pd.date_range(min_time, max_time, freq='15Min')
df = df.reindex(rng)


# # Cumulative rain -> actual rain

# In[112]:



# In[113]:

df['rain'] = df['cum_rain'].diff(periods=2)
df.loc[df['rain'] < 0, 'rain'] = 0 
# interpolate and div 2 to get actual rain every 15 min
df['rain'] = df['rain'].interpolate()
df['rain'] = df['rain'] / 2

# multiply by 4 to get rain rate per hour
df['rain'] = df['rain'] * 2


# In[114]:



# # Interpolate forecast

# In[115]:

# Input forecast data is in mm/hour


# In[116]:

# Remove forecast before latest_rain_time
df.loc[min_time:latest_rain_time, 'forecast'] = None

# Set forecast to rain at latest_rain_time
df.loc[latest_rain_time].forecast = df.loc[latest_rain_time].rain

df['forecast'] = df['forecast'].interpolate()



# # Run model

# In[117]:

df['model_rain'] = df['forecast'].fillna(0) + df['rain'].fillna(0)
df['storage'] = np.nan
df['predict'] = np.nan

# Calculate initial storage
init_storage = f_inv(g_inv(latest_level))
df.loc[latest_level_time, 'storage'] = init_storage

# Run iteration for indexes > latest_level_update
storage = init_storage
df_model = df[(df.index > pd.Timestamp(latest_level_time))]
for i,r in df_model.iterrows():
    rain = df.loc[i - delay, 'model_rain']
    predict = g(f(storage))
    storage = storage + rain - f(storage)
    df.loc[i, 'storage'] = storage
    df.loc[i, 'predict'] = predict




# In[120]:



# # Create export dictionary
# 
# * Round model_rain, level and predict
# * Get current time rounded down to nearest 15 minutes
# * create output dict with the following properties
#     * values
#     * current_time
#     * current_level
#     * text
#     * next_up if in next hour

# In[ ]:




# In[121]:

# Round export columns
df = df.round({'level': 3, 'predict': 3, 'model_rain' : 1})


# In[ ]:




# In[122]:


try:
    current_row = df.loc[pd.to_datetime(current_time, unit='s')]
    current_level = current_row['level']
    if np.isnan(current_level):
        current_level = current_row['predict']
except KeyError:
    print "Can't find row in df that matches current time: "+ time.strftime(time_format, time.gmtime(current_time))
    current_level = None

if verbose:
    print 'currenct level: ' + str(current_level)


# In[123]:


df.timestamp = df.index
df = df.where((pd.notnull(df)), None)
timestamp_vals = [timestmp.value / 1000 for timestmp in df.index.tolist()]
rain_vals = df.model_rain.tolist()
level_vals = df.level.tolist()
predict_vals = df.predict.tolist()
values = []
for n in range(0, len(timestamp_vals)):
    values.append({'timestamp' : timestamp_vals[n], 'rain' : rain_vals[n], 'level' : level_vals[n], 'predict' : predict_vals[n]})


# In[124]:

if current_level > 1.5:
    text = "THE DART IS MASSIVE"
elif current_level > 0.7:
    text = 'YES'
else:
    next_up = df[(df.index > current_time) & (df.index < current_time + delay) & (df.predict > 0.7)].index.min()
    if pd.isnull(next_up):
        text = 'NO'
    else:
        text = "THE DART WILL BE UP SHORTLY"    
if verbose:
    print text


# In[125]:

output = {}       
output['current_time'] = current_time.value / 1000
output['current_level'] = current_level 
output['text'] = text
output['values'] = values


# # Write export to json

# In[84]:

filename = 'dart.json'
with open(os.path.join(fdir, filename), 'w') as f:
    json.dump(output, f)

from local_info import ftp_url, ftp_pass, ftp_user, ftp_dir
"""
ftp = ftplib.FTP(ftp_url)
ftp.login(ftp_user, ftp_pass)
if ftp_dir is not None:
    ftp.cwd(ftp_dir)

ext = os.path.splitext(filename)[1]
if ext in (".txt", ".htm", ".html"):
    ftp.storlines("STOR " + filename, open(filename))
else:
    ftp.storbinary("STOR " + filename, open(filename), 1024)

"""
# In[85]:

if verbose:
    print("---%s seconds ---" % (time.time() - start_time))


# In[ ]:




# In[ ]:




# # COOL STATS : )
# 
# TODO
# * Calculate rain in the last 24 hours

# In[86]:
sys.exit()
database = 'data.db'
river = 'dart'
limit = 200
con = lite.connect(database)
cur = con.cursor()
query = """
        SELECT timestamp, rain, level, forecast 
            from {river}
        ORDER BY timestamp DESC
    """
cur.execute(query.format(river=river, limit=limit))
result = cur.fetchall()
df_all = pd.DataFrame(result, columns=['timestamp', 'cum_rain', 'level', 'forecast'])
df_all.head()


# In[87]:

df_all.timestamp = pd.to_datetime(df_all.timestamp)
df_all = df_all.set_index('timestamp')
df_all = df_all.sort_index()
df_all.head(10)


# In[88]:

# MAX RECORDED LEVEL
print max(df_all.level.fillna(0))


# In[89]:

# LAST TIME THAT THE DART RAN
up_rows = df_all[df_all.level > 0.7].index
last_up = None
if len(up_rows) > 0:
    last_up = pd.to_datetime(max(up_rows))
print 'current_time: ' + str(current_time)

if last_up:
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

    print
    print 'LAST RUNNING ' + last_up_text + ' AGO'
    print last_up_days
else:
    last_up_text = "THE DART HASN'T BEEN UP YET!"
    print last_up_text


# In[90]:

# NUMBER OF DAYS THAT THE DART HAS RUN IN DATA
df_days = df_all.resample('D').max()
#print len(df_days[df_days.level > 0.7])


# NUMBER OF DAYS THAT THE DART HAS RUN IN LAST WEEK
df_last_week = df_days[(current_time - df_days.index) < np.timedelta64(7,'D')]
print 'THE DART HAS RUN ON ' + str(len(df_last_week[df_last_week.level > 0.7])) + ' DAYS IN THE LAST WEEK'

# NUMBER OF DAYS THAT DART HAS RUN IN LAST MONTH
df_last_month = df_days[(current_time - df_days.index) < np.timedelta64(30,'D')]
print 'THE DART HAS RUN ON ' + str(len(df_last_month[df_last_month.level > 0.7])) + ' DAYS IN THE LAST MONTH'


# In[100]:

# SUM OF RAIN IN THE LAST 24 HOURS ... 
# ...A bit more tricky, use cum_rain and somehow take out the max from previous day and today and sum 

# SUM OF RAIN IN THE LAST WEEK
print int(round(sum(df_last_week.cum_rain.fillna(0))))

# SUM OF RAIN IN THE LAST MONTH
print int(round(sum(df_last_month.cum_rain.fillna(0))))


# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:



