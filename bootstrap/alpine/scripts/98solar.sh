#!/usr/bin/env bash

set -ex

# install required stuff
apk add --no-cache py-pip openssl git gcc build-base python-dev libffi libffi-dev

# install packages for solar transports
# (sshpass -> password passing for SSH commands)
apk add --no-cache rsync sshpass

mkdir -p /opt
cd /opt
git clone https://github.com/openstack/solar.git
cd /opt/solar
sudo sed -i '/ansible.*/ s/^#*/#/' requirements.txt
pip install pbr && pip install -e .
chown -R vagrant: /opt/solar
mkdir -p /etc/solar
echo "solar_db: sqlite:////home/vagrant/solar.db" > /etc/solar/solar.yaml
cat <<EOF  >>/etc/init.d/solar-worker
#!/sbin/runscript
# $Header: $

depend() {
    need net
    need localmount
}

start() {
    ebegin "Starting solar-worker"
    exec start-stop-daemon -b --chdir /tmp --start --user vagrant --make-pidfile --pidfile /tmp/solar-worker.pid --exec solar-worker
    eend $?
}

stop() {
    ebegin "Stopping solar-worker"
    exec start-stop-daemon --stop --user vagrant --pidfile /tmp/solar-worker.pid --exec solar-worker
    eend $?
}

EOF
chmod +x /etc/init.d/solar-worker
rc-update add solar-worker default
