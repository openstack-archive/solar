#!/bin/bash -eux

# TODO(bogdando) add centos7 support
exit 0
echo "==> Installed packages before cleanup"
dpkg --get-selections | grep -v deinstall

# Remove some packages to get a minimal install
echo "==> Removing all linux kernels except the currrent one"
dpkg --list | awk '{ print $2 }' | grep 'linux-image-3.*-generic' | grep -v $(uname -r) | xargs apt-get -y purge
echo "==> Removing linux source"
dpkg --list | awk '{ print $2 }' | grep linux-source | xargs apt-get -y purge
echo "==> Removing documentation"
dpkg --list | awk '{ print $2 }' | grep -- '-doc$' | xargs apt-get -y purge
echo "==> Removing obsolete networking components"
apt-get -y purge ppp pppconfig pppoeconf
echo "==> Removing other oddities"
apt-get -y purge popularity-contest installation-report landscape-common wireless-tools wpasupplicant ubuntu-serverguide

# Clean up the apt cache
apt-get -y autoremove --purge
apt-get -y autoclean
apt-get -y clean

echo "==> Removing man pages"
rm -rf /usr/share/man/*
echo "==> Removing anything in /usr/src but this kernel src"
p2=$(uname -r | cut -d- -f1-2)
mv "/usr/src/linux-headers-${p2}" /tmp
mv /usr/src/linux-headers-$(uname -r) /tmp
rm -rf /usr/src/*
mv "/tmp/linux-headers-${p2}" /usr/src/
mv /tmp/linux-headers-$(uname -r) /usr/src/
echo "==> Removing any docs"
rm -rf /usr/share/doc/*
