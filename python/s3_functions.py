import boto3
from local_info import aws_access_key_id, aws_secret_access_key, region_name, bucket_name
import os
import imageio
import time
import image_processing

s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

RIVER_NAME = "dart"
OUTPUT_FILENAME = RIVER_NAME + ".json"
FDIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_PATH = os.path.join(FDIR, '../html', OUTPUT_FILENAME)

def upload_to_s3(filepath, uploadpath):
    with open(filepath) as data:
        bucket.put_object(Key=uploadpath, Body=data, ContentType="image/png")

def upload_radar_images_to_s3():
  dir_path = "../image/radar"
  for f in os.listdir(dir_path):
    upload_to_s3(os.path.join(dir_path, f), os.path.join('images', f))

  

def list_radar_images_in_s3():
  response = s3.list_objects_v2(Bucket=bucket_name, Prefix="images/")

  # Extract the list of files in the directory
  files = [obj['Key'] for obj in response.get('Contents', [])]
  # remove /images
  files = [f[7:] for f in files]
  return(files)


def flatten_and_upload_all_radar_images_s3():
    start = time.time()
    filenames = os.listdir('/mnt/new/root/operational/isthedartrunning/image/radar/')
    timestamps = [filename.split('.')[0] for filename in filenames]

    existing_filenames = list_radar_images_in_s3()
    existing_timestamps = [filename.split('.')[0] for filename in existing_filenames]

    new_timestamps = [t for t in timestamps if t not in existing_timestamps]
    print(len(timestamps))
    print(len(existing_timestamps))
    print(len(new_timestamps))
    for i, timestamp in enumerate(new_timestamps):
      if i % 100 == 0:
        print(i)
        print(time.time() - start)
      try:
        image = imageio.imread('/mnt/new/root/operational/isthedartrunning/image/radar/' + timestamp + ".png")
      except:
        print("failed to read" + filename)
        continue
      array_bytes = image_processing.flatten_radar_image(image).tobytes()
      s3.put_object(Bucket=bucket_name, Key="images/"+timestamp + ".npz", Body=array_bytes)

    print(time.time() - start)



image_file_extensions = [".jpg", ".png"]

def upload_static_files(bucket, path='../html', ignore_images=True):
    for subdir, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(subdir, file)
            with open(full_path, 'rb') as data:
                print(full_path)
                if ".html" in full_path:
                    bucket.put_object(Key=full_path[len(path)+1:], Body=data, ContentType='text/html')
                elif ".css" in full_path:
                    bucket.put_object(Key=full_path[len(path)+1:], Body=data, ContentType='text/css')
                elif ".jpg" in full_path:
                    if ignore_images:
                        continue
                    bucket.put_object(Key=full_path[len(path)+1:], Body=data, ContentType='image/jpg')
                elif ".png" in full_path:
                    if ignore_images:
                        continue
                    bucket.put_object(Key=full_path[len(path)+1:], Body=data, ContentType='image/png')
                else:
                    bucket.put_object(Key=full_path[len(path)+1:], Body=data)
 
def delete_static_files(bucket, ignore_images=False):
    keys = bucket.objects.all()
    for key in keys:
        print(key)
        if ignore_images:
            if any(image_extension in key.key for image_extension in image_file_extensions):
                return
        print(("delete", key.key))
        key.delete()



def upload_json_s3():
    with open(os.path.join(OUTPUT_PATH)) as data:
        bucket.put_object(Key=OUTPUT_FILENAME, Body=data, ContentType="text/json")