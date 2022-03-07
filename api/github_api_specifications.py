import os

github_api_version = "v3"
github_api_url = "https://api.github.com"
github_max_per_page = getenv('GITHUB_MAX_PER_PAGE']
commits_api_url_tpl = github_api_url + "/repos/{}/{}/commits?since={}&sha={}&per_page=" + github_max_per_page
search_api_url_tpl = github_api_url + "/search/issues?q=type:pr+repo:{}%2F{}+{}"
pull_request_url_tpl = github_api_url + "/repos/{}/{}/pulls/{}"
commits_from_pr_api_url_tpl = pull_request_url_tpl + "/commits"
issue_api_url_tpl = github_api_url + "/repos/{}/{}/issues/{}"
issue_url_tpl = "https://github.com/{}/{}/issues/{}"

github_common_header = {
    "Authorization": "Bearer {}".format(getenv('GITHUB_ACCESS_TOKEN']),
    "Accept": "application/vnd.github.{}+json".format(github_api_version)
}
