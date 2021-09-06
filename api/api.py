from flask import Flask, request
from flask_restful import Api

from changelog_utils import *
from api_root import RootEndPoint
from api_manifest import ManifestEndPoint
from api_changelog import ChangelogApi
from api_label import LabelApi

app = Flask(__name__)
api = Api(app)

health_check_routes = ['/', '/health', '/health/', '/v1', '/v1/', '/v1/health', '/v1/health/']
changelog_routes = ['/changelog', '/changelog/', '/v1/changelog', '/v1/changelog/']
manifest_routes = ['/manifest', '/manifest/', '/v1/manifest', '/v1/manifest/']
tag_routes = ['/label', '/label/', '/v1/label', '/v1/label/']

api.add_resource(RootEndPoint, *health_check_routes)
api.add_resource(ChangelogApi, *changelog_routes)
api.add_resource(ManifestEndPoint, *manifest_routes)
api.add_resource(LabelApi, *tag_routes)

if __name__ == '__main__':
    app.run()
