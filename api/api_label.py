import json

from flask import Response
from flask_restful import Resource

from http_utils import *
from changelog_utils import *

class LabelApi(Resource):
    def post(self):
        body = request.get_json(force=True)

        c = check_mandatory_param(body, 'pr_id')
        if is_not_ok(c):
            return c, 400

        c = check_mandatory_param(body, 'org')
        if is_not_ok(c):
            return c, 400

        c = check_mandatory_param(body, 'repo')
        if is_not_ok(c):
            return c, 400

        pull_request_url = pull_request_url_tpl.format(body['org'], body['repo'], body['pr_id'])
        log_msg("debug", "invoking pull_request_url = {}".format(pull_request_url))
        pr_response = requests.get(pull_request_url, headers=github_common_header)
        c = check_response_code(pr_response, "pr")
        if is_not_ok(c):
            return c, pr_response.status_code

        pr_payload = pr_response.json()

        if 'label' in body and body['label'] is not None:
            target_label = body['label']
        else:
            target_label = pr_payload['base']['ref']

        log_msg("debug", "pr_id = {}, target_label = {}".format(body['pr_id'], target_label))

        commits_from_pr_api_url = commits_from_pr_api_url_tpl.format(body['org'], body['repo'], body['pr_id'])
        log_msg("debug", "invoking commits_from_pr_api_url = {}".format(commits_from_pr_api_url))
        commits_response = requests.get(commits_from_pr_api_url, headers=github_common_header)
        c = check_response_code(commits_response, "commits")
        if is_not_ok(c):
            return c, commits_response.status_code

        commits_list = commits_response.json()

        results = {
            "status": "ok",
            "patched_issues": []
        }

        results['patched_issues'].append({
            "id": body['pr_id'],
            "url": pr_payload['html_url'],
            "title": pr_payload['title'],
            "author": pr_payload['user']['login'],
            "labels": list(map(lambda label: label['name'], pr_payload['labels']))
        })

        known_issues_ids = []
        for commit in commits_list:
            extract_issues_from_text(commit['commit']['message'], body['org'], body['repo'], results['patched_issues'], known_issues_ids)

        for issue in results['patched_issues']:
            if issue['labels'] is None:
                issue['labels'] = []

            issue['labels'].append(target_label)
            labels_payload = json.dumps({"labels": issue['labels']})

            issue_api_url = issue_api_url_tpl.format(body['org'], body['repo'], issue['id'])
            log_msg("debug", "invoking issue_api_url = {}".format(issue_api_url))
            issue_response = requests.patch(issue_api_url, headers=github_common_header, data=labels_payload)
            c = check_response_code(issue_response, "pr")
            if is_not_ok(c):
                log_msg("error", "Issue {} not patched : reason = {}".format(issue['id'], c['reason']))

        return results
