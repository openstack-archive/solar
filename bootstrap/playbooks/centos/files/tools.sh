#!/bin/bash -eux
# Install basic packages and build requirements for ansible/librarian-puppet

PACKAGES="
epel-release
git
make
which
ruby-devel
python-devel
autoconf
gcc-c++
openssh-server
iputils-ping
rsyslog
psmisc
iputils
iptables
less
curl
wget
rsync
vim
screen
tcpdump
strace
"
yum -y install $PACKAGES
exit 0
