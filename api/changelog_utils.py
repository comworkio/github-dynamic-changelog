import re
import requests
from datetime import datetime

from flask import Response
from common_utils import *
from logger_utils import *
from http_utils import *
from bucket_utils import *

from github_api_specifications import *

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

def changelog_from_commits(results, commit_concats, body, only_prs):
    filter_author = None
    if not is_empty_request_field(body, 'filter_author'):
        filter_author = body['filter_author']

    write_bucket = False
    if not is_empty_request_field(body, 'write_bucket') and is_true(body['write_bucket']):
        write_bucket = True

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
        upload_file(write_bucket, "json", results, body['org'], body['repo'])
        return results

    mime = determine_mime_type(body['format'])
    if mime == "text/csv":
        response = "title;url;author\n"
        if not only_prs:
            for result in results['issues']:
                response += "{};{};{}\n".format(result['title'], result['url'], result['author'])
        for result in results['prs']:
            response += "{};{};{}\n".format(result['title'], result['url'], result['author'])
        upload_file(write_bucket, "csv", response, body['org'], body['repo'])
        return Response(response, mimetype=mime)
    elif mime == "text/markdown":
        if only_prs:
            response = "# Changelog since {} for the repository {}/{}\n".format(body['since'], body['org'], body['repo'])
        else:
            response = "# Changelog since {} for the repository {}/{}\n\n## Issues\n\n".format(body['since'], body['org'], body['repo'])
            for result in results['issues']:
                response += "* {} - {} - {}\n".format(result['title'], result['url'], result['author'])
        response += "\n## Pull requests\n\n"
        for result in results['prs']:
            response += "* {} - {} - {}\n".format(result['title'], result['url'], result['author'])
        upload_file(write_bucket, "md", response, body['org'], body['repo'])
        return Response(response, mimetype=mime)
    else:
        if only_prs:
            del results['issues']
        upload_file(write_bucket, "json", results, body['org'], body['repo'])
        return results
