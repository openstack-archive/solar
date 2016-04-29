#!/usr/bin/env bash

set -ex

apk add --no-cache py-pip openssl git gcc build-base python-dev libffi libffi-dev

mkdir -p /opt
cd /opt
git clone https://github.com/openstack/solar.git
cd /opt/solar
sudo sed -i '/ansible.*/ s/^#*/#/' requirements.txt
pip install pbr && pip install -e .
chown -R vagrant: /opt/solar
mkdir -p /etc/solar
echo "solar_db: sqlite:////var/lib/solar.db" > /etc/solar/solar.yaml
