from minio import Minio
from minio.error import S3Error

def upload(file_path, target_name, bucket_name):
    endpoint = os.environ['BUCKET_ENDPOINT']
    access_key = os.environ['BUCKET_ACCESS_KEY']
    secret_key = os.environ['BUCKET_SECRET_KEY']

    client = Minio(endpoint, access_key=access_key, secret_key=secret_key)

    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)

    client.fput_object(bucket_name, target_name, file_path)
