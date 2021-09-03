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
commits_api_url_tpl = github_api_url + "/repos/{}/{}/commits?since={}&sha={}"
search_api_url_tpl = github_api_url + "/search/issues?q=type:pr+repo:{}%2F{}+{}"
issue_from_pr_api_url = github_api_url + "repos/{}/{}/pulls/{}"

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

def log_msg (log_level, message):
    cong_log_level = os.environ['LOG_LEVEL']
    if log_level == "error" or log_level == "ERROR" or log_level == "fatal" or log_level == "FATAL":
        eprint ("[{}] {}".format(log_level, message))
    elif cong_log_level == log_level or cong_log_level == "debug" or cong_log_level == "DEBUG":
        print ("[{}] {}".format(log_level, message))

def is_not_ok(body):
    return not "status" in body or body["status"] != "ok"

def is_response_ok(code):
    ok_codes = [200, 201, 204]
    return any(c == code for c in ok_codes)

def check_response_code(response, api):
    if not is_response_ok(response.status_code):
        return {
            "status": "server_error",
            "reason": "api {} didn't answer correctly: status_code = {}, response = {}".format(api, response.status_code, response.text)
        }
    else:
        return {
            "status": "ok"
        }

def check_mandatory_param(body, name):
    if is_empty_request_field(body, name):
        log_msg("error", "[check_mandatory_param] bad request : missing argument = {}, body = {}".format(name, request.data))
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
        log_msg("error", "[check_iso8601_request_param] bad request {} is not an iso formated date".format(name))

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

        commits_api_url = commits_api_url_tpl.format(body['org'], body['repo'], body['since'], body['ref'])
        log_msg("debug", "invoking commits_api_url = {}".format(commits_api_url))
        commits_response = requests.get(commits_api_url, headers=github_common_header)

        c = check_response_code(commits_response, "commits")
        if is_not_ok(c):
            return c, commits_response.status_code

        results = {
            "status": "ok",
            "issues": []
        }

        max = int(os.environ['PAGE_SIZE'])
        commits_list = commits_response.json()
        commit_concats = []
        i=0
        j=0
        
        for commit in commits_list:
            short_commit = commit['sha'][0:8]
            if i >= max:
                i=0
                j+=1
                commit_concats.append(short_commit)
            elif len(commit_concats) <= j:
                commit_concats.append(short_commit)
                i+=1
            else:
                commit_concats[j] = "{}+{}".format(commit_concats[j], short_commit)
                i+=1

        for commits in commit_concats:
            search_api_url = search_api_url_tpl.format(body['org'], body['repo'], commits)
            log_msg("debug", "invoking search_api_url = {}".format(search_api_url))
            search_response = requests.get(search_api_url, headers=github_common_header)
            c = check_response_code(search_response, "search")
            if is_not_ok(c):
                return c, search_response.status_code

            search_result = search_response.json()
            if "total_count" in search_result and search_result['total_count'] > 0:
                return search_result

        return results

        
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
