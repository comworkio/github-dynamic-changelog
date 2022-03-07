import imp
import json

from os import remove
from os import getenv
from io import open
from minio import Minio

from logger_utils import *

def upload_file(write_bucket, ext, content, org, repo):
    log_msg("debug", "upload_file, write_bucket = {}".format(write_bucket))
    if write_bucket:
        name_file = "{}_{}.{}".format(org, repo, ext)
        path_file = "/tmp/{}".format(name_file)

        log_msg("debug", "upload file to bucket: name_file = {}, path_file = {}".format(name_file, path_file))

        vfile = open(path_file, "wt")
        if "json" == ext:
            vfile.write(json.dumps(content))
        else:
            vfile.write(content)
        vfile.close()

        upload_bucket(path_file, name_file)
        remove(path_file)
    
def upload_bucket(file_path, target_name):
    url = getenv('BUCKET_URL')
    access_key = getenv('BUCKET_ACCESS_KEY')
    secret_key = getenv('BUCKET_SECRET_KEY')
    bucket_name = getenv('BUCKET_NAME')
    bucket_region = getenv('BUCKET_REGION')

    log_msg("debug", "upload_bucket bucket_region = {}, url = {}, bucket_name = {}".format(bucket_region, url, bucket_name))
    if url and access_key and secret_key and bucket_name and bucket_region:
        client = Minio(url, region=bucket_region, access_key=access_key, secret_key=secret_key)
        found = client.bucket_exists(bucket_name)
        if not found:
            log_msg("info", "The bucket {} not exists, creation...".format(bucket_name))
            client.make_bucket(bucket_name)
        log_msg("debug", "Upload {} to {}".format(target_name, bucket_name))
        client.fput_object(bucket_name, target_name, file_path)
