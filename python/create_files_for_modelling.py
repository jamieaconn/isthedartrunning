import os
import modelLib
import imageio
import image_processing
import time
import h5py
import numpy as np
import pandas as pd
import boto3
from io import BytesIO
from local_info import aws_access_key_id, aws_secret_access_key, region_name, bucket_name
import PIL

session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

s3 = session.resource('s3')
bucket = s3.Bucket(bucket_name)


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


csv_buffer = BytesIO()
train_df.to_csv(csv_buffer)
bucket.put_object(Key='modelling_data/train.csv', Body=csv_buffer.getvalue())

csv_buffer = BytesIO()
test_df.to_csv(csv_buffer)
bucket.put_object(Key='modelling_data/test.csv', Body=csv_buffer.getvalue())

start = time.time()

chunks = list()
chunk_size = 2000
num_chunks = len(train_df) // chunk_size + 1
for i in range(num_chunks):
  chunks.append(train_df[i*chunk_size:(i+1)*chunk_size])

for j, chunk in enumerate(chunks):
  filepath = 'modelling_data/train_images_' + str(j) + '.h5'
  uploadpath = 'modelling_data/train_images_' + str(j) + '.h5'
  f = h5py.File(filepath, 'w')
  print("Training data - Chunk: " + str(j) + "/" + str(num_chunks))
  images = np.array([], dtype=np.uint8).reshape(0, 500, 500)
  for i, filename in enumerate(chunk.image_filenames.values):
    if i % 100 == 0:
      print(i)
      print(time.time() - start)
    try:
      image = imageio.imread('../image/radar/' + filename)
      flattened_image = image_processing.flatten_radar_image(image)   
    except:
      print("failed to read" + filename)
      flattened_image = np.zeros((500, 500), dtype=np.uint8) 
    images = np.concatenate((images, np.expand_dims(flattened_image, 0)))

  f.create_dataset('images', data=images, dtype="uint8")
  f.close()
  print(filepath)
  with open(filepath) as data:
    bucket.put_object(Key=uploadpath, Body=data)


chunks = list()
chunk_size = 2000
num_chunks = len(test_df) // chunk_size + 1
for i in range(num_chunks):
  chunks.append(test_df[i*chunk_size:(i+1)*chunk_size])

for j, chunk in enumerate(chunks):
  filepath = 'modelling_data/test_images_' + str(j) + '.h5'
  uploadpath = 'modelling_data/test_images_' + str(j) + '.h5'
  f = h5py.File(filepath, 'w')
  print("Test data - Chunk: " + str(j) + "/" + str(num_chunks))
  images = np.array([], dtype=np.uint8).reshape(0, 500, 500)
  for i, filename in enumerate(chunk.image_filenames.values):
    if i % 100 == 0:
      print(i)
      print(time.time() - start)
    try:
      image = imageio.imread('../image/radar/' + filename)
      flattened_image = image_processing.flatten_radar_image(image)   
    except:
      print("failed to read" + filename)
      flattened_image = np.zeros((500, 500), dtype=np.uint8) 
    images = np.concatenate((images, np.expand_dims(flattened_image, 0)))

  f.create_dataset('images', data=images, dtype="uint8")
  f.close()
  print(filepath)
  with open(filepath) as data:
    bucket.put_object(Key=uploadpath, Body=data)
