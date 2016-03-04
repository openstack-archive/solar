#!/bin/sh -eux
# When the docker0 int is created too early,
# Vagrant picks a wrong IP for its NFS mount.
# W/a by making docker unit to wait for the varrant nfs share
cat <<EOF >>/usr/lib/systemd/system/docker.service
[Service]
ExecStartPre=/usr/bin/grep -q vagrant /etc/mtab
RestartSec=5
Restart=always
EOF
