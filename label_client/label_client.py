import os
import sys
import json
import requests

from label_utils import *

pr_id = os.environ['PR_ID']
org = os.environ['GITHUB_ORGANIZATION']
repo = os.environ['GITHUB_REPOSITORY']
api_url = os.environ['API_URL']
api_user = os.getenv('API_USER')
api_password = os.getenv('API_PASSWORD')

label_endpoint = "{}/v1/label".format(api_url)
payload = json.load({"org": org, "repo": repo, "pr_id": pr_id})

log_msg("debug", "invoking label_endpoint = {}".format(label_endpoint))
label_response = requests.post(label_endpoint, data=payload)
c = check_response_code(label_response, "label")
if is_not_ok(c):
    log_msg("error", "Pr {} not patched : reason = {}".format(pr_id, c['reason']))
