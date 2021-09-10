import os
import re
import sys

def is_not_empty (var):
    if (isinstance(var, bool)):
        return var
    elif (isinstance(var, int)):
        return False
    empty_chars = ["", "null", "nil", "false", "none"]
    return var is not None and not any(c == var.lower() for c in empty_chars)

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

regexp_allowed_branches = r'^([0-9]+.[0-9]+.x|master|develop|main|prod|qa|ppd|preprod)$'
match_allowed_branches = re.compile(regexp_allowed_branches).match

def is_allowed_branch(branch_name):
    return match_allowed_branches(branch_name)

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