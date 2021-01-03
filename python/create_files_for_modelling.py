import os
import modelLib
import imageio
import image_processing
import time
import h5py
import numpy as np
import pandas as pd

start_date='2017-12-10 16:15:00'
end_date='2019-04-14 11:45:0'
df = modelLib.load_dataframe_from_sql("dart", limit=-1)
df = df[(df.index>=start_date) & (df.index < end_date)]
min_time = min(df.index)
max_time = max(df.index)
rng = pd.date_range(min_time, max_time, freq='15Min')
df = df.reindex(rng)
df.level = df.level.fillna(method="pad")


df['rain'] = df['cum_rain'].diff(periods=2)
# negative values from diff are when the rain value resets so we set equal to the cumulative value
df.loc[df['rain'] < 0, 'rain'] = df.loc[df['rain'] < 0, 'cum_rain']
#interpolate the rain values

df['rain'] = df['rain'].interpolate()
df['rain'] = df['rain'].fillna(0)

df["image_filenames"] = df.index.strftime('%Y-%m-%dT%H:%M:00.png')

train_df = df.iloc[:int(df.shape[0]/2),:]
test_df = df.iloc[int(df.shape[0]/2):,:]
train_df.to_csv("train.csv")
test_df.to_csv("test.csv")

f = h5py.File('images.h5', 'w')
start = time.time()

images = np.array([], dtype=np.uint8).reshape(0, 100, 100)
for i, filename in enumerate(train_df.image_filenames.values):
  if i % 100 == 0:
    print i
    print time.time() - start
  try:
    image = imageio.imread('../image/radar/' + filename)
    flattened_image = image_processing.flatten_radar_image(image)   
  except:
    print "failed to read" + filename
    flattened_image = np.zeros((500, 500), dtype=np.uint8) 
  images = np.concatenate((images, np.expand_dims(flattened_image[376:476, 210:310], 0)))


f.create_dataset('train', data=images, dtype="uint8")
images = np.array([], dtype=np.uint8).reshape(0, 100, 100)
for i, filename in enumerate(test_df.image_filenames.values):
  if i % 100 == 0:
    print i
    print time.time() - start
  try:
    image = imageio.imread('../image/radar/' + filename)
    flattened_image = image_processing.flatten_radar_image(image)   
  except:
    print "failed to read" + filename
    flattened_image = np.zeros((500, 500), dtype=np.uint8) 
  images = np.concatenate((images, np.expand_dims(flattened_image[376:476, 210:310], 0)))

f.create_dataset('test', data=images, dtype="uint8")

