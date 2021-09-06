from flask import Response
from flask_restful import Resource

from changelog_utils import *

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

        max = int(os.environ['PAGE_SIZE'])

        filter_author = None
        if not is_empty_request_field(body, 'filter_author'):
            filter_author = body['filter_author']

        filter_message = None
        if not is_empty_request_field(body, 'filter_message'):
            filter_message = body['filter_message']

        mime = "application/json"
        if not is_empty_request_field(body, 'format'):
            mime = format

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