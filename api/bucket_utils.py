import json

from os import remove
from io import open
from minio import Minio
from minio.error import S3Error


def upload_file(write_bucket, ext, content, org, repo):
    if write_bucket:
        name_file = "{}_{}.{}".format(org, repo, ext)
        path_file = "/tmp/{}".format(name_file)

        vfile = open(path_file, "wt")
        if "json" == ext:
            vfile.write(json.dumps(content))
        else:
            vfile.write(content)
        vfile.close()

        upload_bucket(path_file, name_file)
        remove(path_file)
    
def upload_bucket(file_path, target_name):
    endpoint = os.environ['BUCKET_ENDPOINT']
    access_key = os.environ['BUCKET_ACCESS_KEY']
    secret_key = os.environ['BUCKET_SECRET_KEY']
    bucket_name = os.environ['BUCKET_NAME']

    client = Minio(endpoint, access_key=access_key, secret_key=secret_key)

    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)

    client.fput_object(bucket_name, target_name, file_path)
