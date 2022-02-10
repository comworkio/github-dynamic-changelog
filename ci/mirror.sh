#!/bin/bash

REPO_PATH="${PROJECT_HOME}/github-dynamic-changelog/"

cd "${REPO_PATH}" && git pull origin main || :
git push github main 
git push internal main
git push pgitlab main
git push bitbucket main
exit 0
