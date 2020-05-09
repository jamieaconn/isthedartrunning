import os
import modelLib
import imageio
import image_processing
import time
import h5py
import numpy as np

start_date='2017-12-10 16:15:00'
end_date='2019-04-14 11:45:0'
df = modelLib.load_dataframe_from_sql("dart", limit=-1)
df = df[(df.index>=start_date) & (df.index < end_date)]
min_time = min(df.index)
max_time = max(df.index)
rng = pd.date_range(min_time, max_time, freq='15Min')
df = df.reindex(rng)

df.to_csv("~/analysis.csv")


df["image_filenames"] = df.index.strftime('%Y-%m-%dT%H:%M:00.png')

train_df = df.iloc[:int(df.shape[0]/5),:]
test_df = df.iloc[int(df.shape[0]/5):int(df.shape[0]/10),:]
start = time.time()

train_images = np.array([], dtype=np.uint8).reshape(0, 250, 250)
for i, filename in enumerate(train_df.image_filenames.values):
  if i % 100 == 0:
    print i
    print time.time() - start
  try:
    image = imageio.imread('../image/radar/' + filename)
    flattened_image = image_processing.flatten_radar_image(image)   
  except:
    print "failed to read" + filename
    flattened_image = np.zeros((500, 500), dtype=uint8) 
  #imageio.imwrite('~/images'+filename, flattened_image[250:,:250])
  train_images = np.concatenate((train_images, np.expand_dims(flattened_image[250:,:250], 0)))
#f.create_dataset(filename, (500, 500), data=flattened_image)

