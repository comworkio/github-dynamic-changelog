#!/bin/bash

REPO_PATH="/home/centos/github-dynamic-changelog/"

cd "${REPO_PATH}" && git pull origin main || :
git push github main 
git push internal main
git push pgitlab main
exit 0
