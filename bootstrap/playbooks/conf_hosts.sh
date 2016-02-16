#!/bin/bash -eux
# Misc host setup actions for Vagrantfile

# Configure hosts entries in the /etc/hosts
[ -z "${1}" ] && exit 1
echo "::1 localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
" >/etc/hosts
while (( "$#" )); do
  echo "${1}" >> /etc/hosts
  shift
done

# This is for docker containers
rsyslogd >/dev/null 2>&1 || /bin/true
exit 0

# DNS, NTP etc. may go here as well
