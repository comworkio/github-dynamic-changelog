from flask import Flask, request
from flask_restful import Api

from api_root import RootEndPoint
from api_manifest import ManifestEndPoint
from api_changelog import ChangelogApi
from api_changelog_from_sha import ChangelogFromShaApi
from api_label import LabelApi

app = Flask(__name__)
api = Api(app)

health_check_routes = ['/', '/health', '/health/', '/v1', '/v1/', '/v1/health', '/v1/health/']
changelog_routes = ['/changelog', '/changelog/', '/v1/changelog', '/v1/changelog/']
changelog_from_sha_routes = ['/changelog/sha', '/changelog/sha', '/v1/changelog/sha', '/v1/changelog/sha']
manifest_routes = ['/manifest', '/manifest/', '/v1/manifest', '/v1/manifest/']
tag_routes = ['/label', '/label/', '/v1/label', '/v1/label/']

api.add_resource(RootEndPoint, *health_check_routes)
api.add_resource(ChangelogApi, *changelog_routes)
api.add_resource(ChangelogFromShaApi, *changelog_from_sha_routes)
api.add_resource(ManifestEndPoint, *manifest_routes)
api.add_resource(LabelApi, *tag_routes)

if __name__ == '__main__':
    app.run()
