import os
import modelLib
import imageio
import image_processing
import time
import h5py

start_date='2017-12-10 16:15:00'
end_date='2019-04-14 11:45:0'
df = modelLib.load_dataframe_from_sql("dart", limit=-1)
df = df[(df.index>=start_date) & (df.index < end_date)]
df.to_csv("~/analysis.csv")


df["image_filenames"] = df.index.strftime('%Y-%m-%dT%H:%M:00.png')


for i, filename in enumerate(df.image_filenames.values):
  if i % 100 == 0:
    print i
    print time.time() - start
  try:
    image = imageio.imread('../image/radar/' + filename)
    flattened_image = image_processing.flatten_radar_image(image)   
  except:
    print "failed to read" + filename
    flattened_image = np.zeros((500, 500)) 
  break
