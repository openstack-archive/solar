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

SOLAR_DB_BACKEND=${SOLAR_DB_BACKEND:-riak}

SSH_OPTIONS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

dos.py erase ${ENV_NAME} || true
mkdir -p tmp

mkdir -p logs
rm -rf logs/*
ENV_NAME=${ENV_NAME} SLAVES_COUNT=${SLAVES_COUNT} IMAGE_PATH=${IMAGE_PATH} CONF_PATH=${CONF_PATH} python utils/jenkins/env.py create_env

SLAVE_IPS=`ENV_NAME=${ENV_NAME} python utils/jenkins/env.py get_slaves_ips`
ADMIN_IP=`ENV_NAME=${ENV_NAME} python utils/jenkins/env.py get_admin_ip`

# Wait for master to boot
elapsed_time=0
master_wait_time=30
while true
do
  report=$(sshpass -p ${ADMIN_PASSWORD} ssh ${SSH_OPTIONS} ${ADMIN_USER}@${ADMIN_IP} echo ok || echo not ready)

  if [ "${report}" = "ok" ]; then
    break
  fi

  if [ "${elapsed_time}" -gt "${master_wait_time}" ]; then
    exit 2
  fi

  sleep 1
  let elapsed_time+=1
done

sshpass -p ${ADMIN_PASSWORD} rsync -rz . -e "ssh ${SSH_OPTIONS}" ${ADMIN_USER}@${ADMIN_IP}:/home/vagrant/solar --include bootstrap/playbooks --exclude "bootstrap/*" --exclude .tox --exclude tmp --exclude x-venv

set +e
sshpass -p ${ADMIN_PASSWORD} ssh ${SSH_OPTIONS} ${ADMIN_USER}@${ADMIN_IP} bash -s <<EOF
set -x

export PYTHONWARNINGS="ignore"

sudo rm -rf /vagrant
sudo mv /home/vagrant/solar /vagrant

sudo chown -R ${ADMIN_USER} ${INSTALL_DIR}
sudo SOLAR_DB_BACKEND=${SOLAR_DB_BACKEND} ansible-playbook -v -i \"localhost,\" -c local ${INSTALL_DIR}/bootstrap/playbooks/solar.yaml

set -e

# wait for riak

if [ $SOLAR_DB_BACKEND == "riak" ]
then
   sudo docker exec vagrant_riak_1 riak-admin wait_for_service riak_kv;
elif [ $SOLAR_DB_BACKEND == "postgres" ]
then
   # TODO: Should be replaced with something smarter
   sleep 5
fi

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

deploy_res=$?

# collect logs
sshpass -p ${ADMIN_PASSWORD} scp ${SSH_OPTIONS} ${ADMIN_USER}@${ADMIN_IP}:/var/log/solar/solar.log logs/

if [ "${deploy_res}" -eq "0" ];then
  dos.py erase ${ENV_NAME}
else
  dos.py snapshot ${ENV_NAME} ${ENV_NAME}.snapshot
  dos.py destroy ${ENV_NAME}
  echo "To revert snapshot please run: dos.py revert ${ENV_NAME} ${ENV_NAME}.snapshot"
fi

exit ${deploy_res}
