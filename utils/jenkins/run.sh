#!/bin/bash
set -xe

# for now we assume that master ip is 10.0.0.2 and slaves ips are 10.0.0.{3,4,5,...}
ADMIN_PASSWORD=vagrant
ADMIN_USER=vagrant
INSTALL_DIR=/vagrant

ENV_NAME=${ENV_NAME:-solar-example}
SLAVES_COUNT=${SLAVES_COUNT:-0}
CONF_PATH=${CONF_PATH:-utils/jenkins/default.yaml}

IMAGE_PATH=${IMAGE_PATH:-bootstrap/output-qemu/ubuntu1404}
TEST_SCRIPT=${TEST_SCRIPT:-/vagrant/examples/hosts_file/hosts.py}
DEPLOY_TIMEOUT=${DEPLOY_TIMEOUT:-60}

dos.py erase ${ENV_NAME} || true
mkdir -p tmp
ENV_NAME=${ENV_NAME} SLAVES_COUNT=${SLAVES_COUNT} IMAGE_PATH=${IMAGE_PATH} CONF_PATH=${CONF_PATH} python utils/jenkins/env.py create_env

SLAVE_IPS=`ENV_NAME=${ENV_NAME} python utils/jenkins/env.py get_slaves_ips`
ADMIN_IP=`ENV_NAME=${ENV_NAME} python utils/jenkins/env.py get_admin_ip`

# Wait for master to boot
sleep 30

sshpass -p ${ADMIN_PASSWORD} rsync -rz . -e "ssh -o StrictHostKeyChecking=no" ${ADMIN_USER}@${ADMIN_IP}:/home/vagrant/solar --include bootstrap/playbooks --exclude "bootstrap/*" --exclude .tox --exclude tmp --exclude x-venv

sshpass -p ${ADMIN_PASSWORD} ssh -o StrictHostKeyChecking=no ${ADMIN_USER}@${ADMIN_IP} bash -s <<EOF
set -x
export PYTHONWARNINGS="ignore"

sudo rm -rf /vagrant
sudo mv /home/vagrant/solar /vagrant

sudo chown -R ${ADMIN_USER} ${INSTALL_DIR}
sudo ansible-playbook -v -i \"localhost,\" -c local ${INSTALL_DIR}/bootstrap/playbooks/solar.yaml

set -e

# wait for riak
sudo docker exec vagrant_riak_1 riak-admin wait_for_service riak_kv

export SOLAR_CONFIG_OVERRIDE="/.solar_config_override"

solar repo update templates ${INSTALL_DIR}/utils/jenkins/repository

solar resource create nodes templates/nodes ips="${SLAVE_IPS}" count="${SLAVES_COUNT}"
bash -c "${TEST_SCRIPT}"

solar changes stage
solar changes process
solar orch run-once

elapsed_time=0
while true
do
  report=\$(solar o report)

  errors=\$(echo "\${report}" | grep -e ERROR | wc -l)
  if [ "\${errors}" != "0" ]; then
    solar orch report
    echo FAILURE
    exit 1
  fi

  running=\$(echo "\${report}" | grep -e PENDING -e INPROGRESS | wc -l)
  if [ "\${running}" == "0" ]; then
    solar orch report
    echo SUCCESS
    exit 0
  fi

  if [ "\${elapsed_time}" -gt "${DEPLOY_TIMEOUT}" ]; then
    solar orch report
    echo TIMEOUT
    exit 2
  fi

  sleep 5
  let elapsed_time+=5
done
EOF

if [ "$?" -eq "0" ];then
  dos.py erase ${ENV_NAME} || true
fi
