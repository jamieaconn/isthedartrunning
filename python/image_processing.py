import numpy as np
import time
import imageio
import time
import os
import random
import h5py
import upload_model_data_s3

# List of colours used in order of rainfall rate
colours = np.array([
    [199,191,193,128],  
    [0,0,0,0],
    [  0,   0, 254, 255],
    [ 50, 101, 254, 255],
    [127, 127,   0, 255],
    [254, 203,   0, 255],
    [254, 152,   0, 255],
    [254,   0,   0, 255],
    [254,   0, 254, 255],
    [229, 254, 254, 255]
])

# This converts each rgb value to a single unique number (don't care about alphas)
w = np.array([1, 256, 256**2, 0])
colour_values = colours.dot(w)

# Input 500*500*3 image and return 500*500 image
def flatten_radar_image(image):

    flattened_image = image.dot(w)

    final_image = np.zeros((500, 500), dtype=int)
    for i, v in enumerate(list(colour_values)):
      # The first two colours, white and grey are both 0 rainfall
      p = 0 if i==1 else i
      final_image[flattened_image==v]=p
    return(final_image.astype(np.uint8))

def unflatten_radar_image(image):
  return(colours[image])

def upload_all_images_s3():
    start = time.time()

    filenames = os.listdir('../image/radar')

    for i, filename in enumerate(filenames):
      if i % 100 == 0:
        print(i)
        print(time.time() - start)
      try:
        image = imageio.imread('../image/radar/' + filename)
      except:
        print("failed to read" + filename)
        continue
      flattened_image = flatten_radar_image(image)
      imageio.imwrite('temp.png', flattened_image)
      upload_model_data_s3.upload_to_s3('temp.png', 'images/'+filename)

    print(time.time() - start)
