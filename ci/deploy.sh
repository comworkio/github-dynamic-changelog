#!/usr/bin/env bash

echo "GITHUB_ACCESS_TOKEN=${GITHUB_ACCESS_TOKEN}" > .env
docker rmi -f "comworkio/github-dynamic-changelog:latest" || :
docker-compose -f docker-compose-intra.yml up -d --force-recreate
