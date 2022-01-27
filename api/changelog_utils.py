import os
import sys
import re
import requests
from datetime import datetime

from flask import request, Response
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
regexp_external_issues = r'#([^\#\/]+)\/([^\#\/]+)\/issues\/([0-9]+)'
pattern_regexp_issues = re.compile(regexp_issues)
pattern_regexp_external_issues = re.compile(regexp_external_issues)

regexp_pull_url = r'.*\/pull.*'
match_pull_url = re.compile(regexp_pull_url).match

def extract_issues_from_text(text, org, repo, issues, known_issues_ids):
    if text.startswith("Merge"):
        return None

    issues_parameters = pattern_regexp_external_issues.search(text)
    issues_id = None
    if issues_parameters is not None:
        issue_params_groups = issues_parameters.groups()
        if len(issue_params_groups) >= 3:
            org = issue_params_groups[0]
            repo = issue_params_groups[1]
            issues_id = [issue_params_groups[2]]

    if issues_id is None:
        issues_id_groups = pattern_regexp_issues.search(text)
        if issues_id_groups is None:
            return None
        issues_id = issues_id_groups.groups()

    if issues_id is None:
        return None

    for issue_id in issues_id:
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

def current_datetime_iso(body):
    current_date = datetime.now()
    body['since'] = current_date.isoformat()

def changelog_from_commits(results, commit_concats, body):
    filter_author = None
    if not is_empty_request_field(body, 'filter_author'):
        filter_author = body['filter_author']

    if "since" not in body:
        current_datetime_iso(body)

    c = check_iso8601_request_param(body, 'since')
    if is_not_ok(c):
        current_datetime_iso(body)

    for commits in commit_concats:
        search_api_url = search_api_url_tpl.format(body['org'], body['repo'], commits)
        log_msg("debug", "invoking search_api_url = {}".format(search_api_url))
        search_response = requests.get(search_api_url, headers=github_common_header)
        c = check_response_code(search_response, "search")
        if is_not_ok(c):
            return c, search_response.status_code

        search_result = search_response.json()
        
        if "total_count" in search_result and search_result['total_count'] > 0:
            for issue in search_result['items']:
                id = issue['url'].rsplit('/',1)[1]
                issue_response = requests.get(issue['url'], headers=github_common_header)
                c = check_response_code(search_response, "issue")
                if is_not_ok(c):
                    results['prs'].append({
                        'id': id,
                        'url': issue['url']
                    })
                else:
                    details = issue_response.json()
                    author = details['user']['login']

                    if author == filter_author:
                        continue

                    results['prs'].append({
                        'id': id,
                        'url': issue['html_url'],
                        'title': details['title'],
                        'author': author,
                        'labels': list(map(lambda label: label['name'], details['labels']))
                    })

    if is_empty_request_field(body, 'format'):
        return results

    mime = determine_mime_type(body['format'])
    if mime == "text/csv":
        response = "title;url;author\n"
        for result in results['issues']:
            response += "{};{};{}\n".format(result['title'], result['url'], result['author'])
        for result in results['prs']:
            response += "{};{};{}\n".format(result['title'], result['url'], result['author'])
        return Response(response, mimetype=mime)
    elif mime == "text/markdown":
        response = "# Changelog since {} for the repository {}/{}\n\n## Issues\n\n".format(body['since'], body['org'], body['repo'])
        for result in results['issues']:
            response += "* {} - {} - {}\n".format(result['title'], result['url'], result['author'])
        response += "\n## Pull requests\n\n"
        for result in results['prs']:
            response += "* {} - {} - {}\n".format(result['title'], result['url'], result['author'])
        return Response(response, mimetype=mime)
    else:
        return results
