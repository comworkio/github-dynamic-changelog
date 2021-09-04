#!/bin/bash

REPO_PATH="/home/centos/github-dynamic-changelog/"

cd "${REPO_PATH}" && git pull origin main || :
docker-compose -f docker-compose-comwork.yml up -d --force-recreate
