import os

github_api_version = "v3"
github_api_url = "https://api.github.com"
github_max_per_page = os.environ['GITHUB_MAX_PER_PAGE']
commits_api_url_tpl = github_api_url + "/repos/{}/{}/commits?since={}&sha={}&per_page=" + github_max_per_page
search_api_url_tpl = github_api_url + "/search/issues?q=type:pr+repo:{}%2F{}+{}"
issue_api_url_tpl = github_api_url + "/repos/{}/{}/issues/{}"
issue_url_tpl = "https://github.com/{}/{}/issues/{}"

github_common_header = {
    "Authorization": "Bearer {}".format(os.environ['GITHUB_ACCESS_TOKEN']),
    "Accept": "application/vnd.github.{}+json".format(github_api_version)
}
