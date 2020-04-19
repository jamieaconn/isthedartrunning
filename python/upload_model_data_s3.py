import boto3
from local_info import aws_access_key_id, aws_secret_access_key, region_name, bucket_name
import os
import modelLib

session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)
s3 = session.resource('s3')
bucket = s3.Bucket(bucket_name)

def upload_to_s3(filepath, uploadpath):
    with open(filepath) as data:
        bucket.put_object(Key=uploadpath, Body=data, ContentType="text/json")

def upload_radar_images_to_s3():
  dir_path = "../image/radar"
  for f in os.listdir(dir_path):
    upload_to_s3(os.path.join(dir_path, f), os.path.join('images', f))

def upload_data_csv_to_s3():
  df = modelLib.load_dataframe_from_sql("dart", limit=-1)
  df.to_csv("../data.csv")
  upload_to_s3("../data.csv", "data.csv")
  
