import re

from flask import request

from logger_utils import *
from common_utils import *

def determine_mime_type (mime):
    known_mime_types = ["application/json", "text/csv", "text/markdown"]
    if mime is None:
        return known_mime_types[0]
    
    for m in known_mime_types:
        if mime.lower().startswith(m):
            return m

    return known_mime_types[0]

def is_empty_request_field (body, name):
    return not name in body or is_empty(body[name])

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