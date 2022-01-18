from flask import Response
from flask_restful import Resource

from changelog_utils import *

class ChangelogFromShaApi(Resource):
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

        results = {
            "status": "ok",
            "prs": [],
            "issues": []
        }

        return changelog_from_commits(results, body['sha'], body)
