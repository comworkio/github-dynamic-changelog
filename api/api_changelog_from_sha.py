from flask import Response
from flask_restful import Resource

from changelog_utils import *

class ChangelogApi(Resource):
    def post(self):
        body = request.get_json(force=True)

        c = check_mandatory_param(body, 'org')
        if is_not_ok(c):
            return c, 400

        c = check_mandatory_param(body, 'repo')
        if is_not_ok(c):
            return c, 400

        c = check_mandatory_param(body, 'sha')
        if is_not_ok(c):
            return c, 400

        commits_api_url = commits_api_url_tpl.format(body['org'], body['repo'], body['since'], body['ref'])
        log_msg("debug", "invoking commits_api_url = {}".format(commits_api_url))
        commits_response = requests.get(commits_api_url, headers=github_common_header)

        c = check_response_code(commits_response, "commits")
        if is_not_ok(c):
            return c, commits_response.status_code

        commits_list = commits_response.json()
        page = 1
        len_page = len(commits_list)
        while len_page >= int(github_max_per_page):
            commits_api_url_paged = commits_api_url + "&page={}".format(page)
            log_msg("debug", "len_page = {}, invoking commits_api_url_paged = {}".format(len_page, commits_api_url_paged))
            commits_response_paged = requests.get(commits_api_url_paged, headers=github_common_header)
            c = check_response_code(commits_response_paged, "commits")
            if is_not_ok(c):
                break

            page_results = commits_response_paged.json()
            len_page = len(page_results)
            if len_page > 0 and 'sha' in page_results[0]:
                commits_list += page_results
            page += 1

        results = {
            "status": "ok",
            "prs": [],
            "issues": []
        }

        return changelog_from_commits(results, body['sha'], body)
