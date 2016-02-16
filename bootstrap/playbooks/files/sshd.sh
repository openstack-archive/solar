#!/bin/bash -eux
mkdir -p /var/run/sshd
echo "UseDNS no" >> /etc/ssh/sshd_config
