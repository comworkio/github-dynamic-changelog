import json

from os import remove
from os import getenv
from io import open
from minio import Minio

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
    endpoint = getenv('BUCKET_ENDPOINT')
    access_key = getenv('BUCKET_ACCESS_KEY')
    secret_key = getenv('BUCKET_SECRET_KEY')
    bucket_name = getenv('BUCKET_NAME')

    if endpoint and access_key and secret_key and bucket_name:
        client = Minio(endpoint, access_key=access_key, secret_key=secret_key)
        found = client.bucket_exists(bucket_name)
        if not found:
            client.make_bucket(bucket_name)
        client.fput_object(bucket_name, target_name, file_path)
