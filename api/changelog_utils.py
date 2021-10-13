import os
import sys
import re
import requests

from flask import request
from github_api_specifications import *

def is_not_empty (var):
    if (isinstance(var, bool)):
        return var
    elif (isinstance(var, int)):
        return False
    empty_chars = ["", "null", "nil", "false", "none"]
    return var is not None and not any(c == var.lower() for c in empty_chars)

def determine_mime_type (mime):
    known_mime_types = ["application/json", "text/csv", "text/markdown"]
    if mime is None:
        return known_mime_types[0]
    
    for m in known_mime_types:
        if mime.lower().startswith(m):
            return m

    return known_mime_types[0]

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

regexp_data_iso = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
match_iso8601 = re.compile(regexp_data_iso).match

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

regexp_issues = r'#[^\#]*?([0-9]+)'
pattern_regexp_issues = re.compile(regexp_issues)

regexp_pull_url = r'.*\/pull.*'
match_pull_url = re.compile(regexp_pull_url).match

def extract_issues_from_text(text, org, repo, issues, known_issues_ids):
    if text.startswith("Merge"):
        return None

    issues_id = pattern_regexp_issues.search(text)
    if issues_id is None:
        return None

    for issue_id in issues_id.groups():
        log_msg("debug", "extract issue_id = {} in text = {}".format(issue_id, text))
        if issue_id not in known_issues_ids:
            known_issues_ids.append(issue_id)
            issue_api_url = issue_api_url_tpl.format(org, repo, issue_id)
            log_msg("debug", "invoking issue_api_url = {}".format(issue_api_url))
            issue_response = requests.get(issue_api_url, headers=github_common_header)
            c = check_response_code(issue_response, "issue")
            if is_not_ok(c):
                continue
            else:
                details = issue_response.json()
                if match_pull_url(details['html_url']):
                    continue
                issues.append({
                    "id": issue_id,
                    "url": details['html_url'],
                    "title": details['title'],
                    "author": details['user']['login'],
                    "labels": list(map(lambda label: label['name'], details['labels']))
                })
