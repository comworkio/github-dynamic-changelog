#!/bin/bash

v="$(git log  --pretty=oneline --since=${1}.days| awk '{print $1}')"
jq -nc '$ARGS.positional' --args ${v[@]}
