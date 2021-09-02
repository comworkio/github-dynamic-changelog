from flask import Flask, request

## https://github.com/flask-restful/flask-restful/pull/913
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func

from flask_restful import Resource, Api

from subprocess import check_output
from multiprocessing import Process
import os
import json
import sys
import re
import requests

app = Flask(__name__)
api = Api(app)

github_api_version = "v3"
github_api_url = "https://api.github.com"
commits_api_url_tpl = github_api_url + "/repos/{}/{}/commits?since{}&sha={}"

github_common_header = {
    "Authorization": "Bearer {}".format(os.environ['GITHUB_ACCESS_TOKEN']),
    "Accept": "application/vnd.github.{}+json".format(github_api_version)
}

def is_not_empty (var):
    if (isinstance(var, bool)):
        return var
    elif (isinstance(var, int)):
        return False
    empty_chars = ["", "null", "nil", "false", "none"]
    return var is not None and not any(c == var.lower() for c in empty_chars)

def is_empty (var):
    return not is_not_empty(var)

def is_empty_request_field (body, name):
    return not name in body or is_empty(body[name])

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def is_not_ok(body):
    return not "status" in body or body["status"] != "ok"

def is_response_ok(code):
    ok_codes = [200, 201, 204]
    return any(c == code for c in ok_codes)

def check_response_code(code, api):
    if not is_response_ok(code):
        return {
            "status": "server_error",
            "reason": "api {} didn't answer correctly: status_code = {}".format(api, code)
        }
    else:
        return {
            "status": "ok"
        }

def check_mandatory_param(body, name):
    if is_empty_request_field(body, name):
        eprint("[check_mandatory_param] bad request : missing argument = {}, body = {}".format(name, request.data))
        return {
            "status": "bad_request",
            "reason": "missing {} argument".format(name)
        }
    else:
        return {
            "status": "ok"
        }

regex_data_iso = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
match_iso8601 = re.compile(regex_data_iso).match

def check_iso8601_request_param(body, name):
    try:            
        if not is_empty_request_field(body, name) and match_iso8601(body[name]) is not None:
            return {
                "status": "ok"
            }
    except:
        pass
    return {
        "status": "bad_request",
        "reason": "argument {} is not an iso format date".format(name)
    }

class ChangelogApi(Resource):
    def post(self):
        body = request.get_json(force=True)

        c = check_mandatory_param(body, 'ref')
        if is_not_ok(c):
            return c, 400

        c = check_mandatory_param(body, 'org')
        if is_not_ok(c):
            return c, 400

        c = check_mandatory_param(body, 'repo')
        if is_not_ok(c):
            return c, 400

        c = check_iso8601_request_param(body, 'since')
        if is_not_ok(c):
            return c, 400

        commits_req = requests.get(commits_api_url_tpl.format(body['org'], body['repo'], body['since'], body['ref']))
        c = check_response_code(commits_req.status_code, "commits")
        if is_not_ok(c):
            return c, 500

        return commits_req.json()
        
class RootEndPoint(Resource):
    def get(self):
        return {
            'status': 'ok',
            'alive': True
        }

class ManifestEndPoint(Resource):
    def get(self):
        try:
            with open(os.environ['MANIFEST_FILE_PATH']) as manifest_file:
                manifest = json.load(manifest_file)
                return manifest
        except IOError as err:
            return {
                'status': 'error', 
                'reason': err
            }, 500

health_check_routes = ['/', '/health', '/health/', '/v1', '/v1/', '/v1/health', '/v1/health/']
changelog_routes = ['/changelog', '/changelog/', '/v1/changelog', '/v1/changelog/']
manifest_routes = ['/manifest', '/manifest/', '/v1/manifest', '/v1/manifest/']

api.add_resource(RootEndPoint, *health_check_routes)
api.add_resource(ChangelogApi, *changelog_routes)
api.add_resource(ManifestEndPoint, *manifest_routes)

if __name__ == '__main__':
    app.run()
