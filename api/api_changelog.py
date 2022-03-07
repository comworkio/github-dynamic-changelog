from flask_restful import Resource

from http_utils import *
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

        c = check_iso8601_request_param(body, 'since')
        if is_not_ok(c):
            return c, 400

        c = check_mandatory_param(body, 'ref')
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

        max = int(getenv('PAGE_SIZE'])

        filter_author = None
        if not is_empty_request_field(body, 'filter_author'):
            filter_author = body['filter_author']

        filter_message = None
        if not is_empty_request_field(body, 'filter_message'):
            filter_message = body['filter_message']

        mime = "application/json"
        if not is_empty_request_field(body, 'format'):
            mime = format

        only_prs = not is_empty_request_field(body, 'only_prs')

        commit_concats = []
        known_issues_ids = []
        i=0
        j=0
        
        for commit in commits_list:
            short_commit = commit['sha'][0:8]

            if commit['commit']['author']['name'] == filter_author or commit['commit']['committer']['name'] == filter_author:
                continue

            if filter_message is not None and filter_message.lower() in commit['commit']['message'].lower():
                continue

            if not only_prs:
                extract_issues_from_text(commit['commit']['message'], body['org'], body['repo'], results['issues'], known_issues_ids)

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

        return changelog_from_commits(results, commit_concats, body, only_prs)
