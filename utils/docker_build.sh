#!/bin/bash
set -e

# should be executed from directory with required Dockerfile
name_w_tags=$1

if [[ -z "$name_w_tags" ]]; then
    name_w_tags='solarproject/solar-celery:latest'
fi

echo "Building image with name $name_w_tags"
docker build -t "$name_w_tags" .
docker push "$name_w_tags"

