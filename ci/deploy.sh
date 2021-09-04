#!/bin/bash

REPO_PATH="/home/centos/github-dynamic-changelog/"

cd "${REPO_PATH}" && git pull origin main || :
echo "GITHUB_ACCESS_TOKEN=${GITHUB_ACCESS_TOKEN}" > .env
docker-compose -f docker-compose-comwork.yml up -d --force-recreate
