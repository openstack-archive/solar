#! /bin/bash
export SOLAR_CONFIG_OVERRIDE="/.solar_config_override"
sudo pip install netaddr

pushd /tmp > /dev/null
rm -rf k8s
rm -rf /var/lib/solar/repositories/k8s
git clone https://github.com/pigmej/solar-k8s.git k8s
solar repo import -l k8s
pushd k8s
cp config.yaml.sample config.yaml
./setup_k8s.py deploy
solar changes stage
solar changes process
solar orch run-once
solar orch report -w 1200 last
