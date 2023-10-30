import boto3
from local_info import aws_access_key_id, aws_secret_access_key, region_name, bucket_name
import os
import modelLib
import imageio
import time
import image_processing

session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)
s3 = session.resource('s3')
bucket = s3.Bucket(bucket_name)

RIVER_NAME = "dart"
OUTPUT_FILENAME = RIVER_NAME + ".json"
FDIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_PATH = os.path.join(FDIR, '../html', OUTPUT_FILENAME)

def upload_to_s3(filepath, uploadpath):
    with open(filepath) as data:
        bucket.put_object(Key=uploadpath, Body=data, ContentType="text/json")

def upload_radar_images_to_s3():
  dir_path = "../image/radar"
  for f in os.listdir(dir_path):
    upload_to_s3(os.path.join(dir_path, f), os.path.join('images', f))

def upload_sql_to_s3_as_csv():
  df = modelLib.load_dataframe_from_sql("dart", limit=-1)
  df.to_csv("../data.csv")
  upload_to_s3("../data.csv", "data.csv")
  

def list_radar_images_in_s3():
  existing_image_filenames = [obj.key[len("images/"):] for obj in bucket.objects.filter(Prefix="images/")]
  return(existing_image_filenames)


def flatten_and_upload_all_radar_images_s3():
    start = time.time()
    filenames = os.listdir('../image/radar')
    existing_image_filenames = list_radar_images_in_s3()

    new_filenames = [f for f in filenames if f not in existing_image_filenames]

    len(new_filenames)
    for i, filename in enumerate(new_filenames):
      if i % 100 == 0:
        print(i)
        print(time.time() - start)
      try:
        image = imageio.imread('../image/radar/' + filename)
      except:
        print("failed to read" + filename)
        continue
      flattened_image = image_processing.flatten_radar_image(image)
      imageio.imwrite('temp.png', flattened_image)
      upload_to_s3('temp.png', 'images/'+filename)

    print(time.time() - start)



image_file_extensions = [".jpg", ".png"]

def upload_static_files(bucket=bucket, path='../html', ignore_images=True):
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
 
def delete_static_files(bucket=bucket, ignore_images=False):
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