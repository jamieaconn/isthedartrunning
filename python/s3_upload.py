import boto3
import os
 
from local_info import aws_access_key_id, aws_secret_access_key, region_name, bucket_name


image_file_extensions = [".jpg", ".png"]

def upload_files(bucket, path, ignore_images=True):
    print "test"
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
 
def delete_all_files(bucket, ignore_images=False):
    keys = bucket.objects.all()
    for key in keys:
        print(key)
        if ignore_images:
            if any(image_extension in key.key for image_extension in image_file_extensions):
                return
        print("delete", key.key)
        key.delete()


if __name__ == "__main__":
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)
    #delete_all_files(bucket, ignore_images=True)
    upload_files(bucket, '../html', ignore_images=False)

