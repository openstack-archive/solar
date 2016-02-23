#!/bin/bash -eux
# Install basic packages and build requirements for ansible/librarian-puppet

PACKAGES="
git
make
ruby-dev
python-dev
autoconf
g++
openssh-server
iputils-ping
rsyslog
psmisc
iputils-ping
iptables
less
curl
wget
rsync
elvis-tiny
screen
tcpdump
strace
"
apt-get -y install $PACKAGES
exit 0
