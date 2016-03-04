#!/bin/sh -eux
# Remove Linux headers
yum -y remove kernel-devel kernel-headers
yum -y clean all

# Remove Virtualbox specific files
rm -rf /usr/src/vboxguest* /usr/src/virtualbox-ose-guest*
rm -rf *.iso *.iso.? /tmp/vbox /home/vagrant/.vbox_version

# Cleanup log files
find /var/log -type f | while read f; do echo -ne '' > $f; done;

# remove under tmp directory
rm -rf /tmp/*

# remove interface persistent
rm -f /etc/udev/rules.d/70-persistent-net.rules

for ifcfg in $(ls /etc/sysconfig/network-scripts/ifcfg-*)
do
    if [ "$(basename ${ifcfg})" != "ifcfg-lo" ]
    then
        sed -i '/^UUID/d'   /etc/sysconfig/network-scripts/ifcfg-eth0
        sed -i '/^HWADDR/d' /etc/sysconfig/network-scripts/ifcfg-eth0
    fi
done

dd if=/dev/zero of=/EMPTY bs=1M
rm -rf /EMPTY

# Make sure we wait until all the data is written to disk, otherwise
# Packer might quite too early before the large files are deleted
sync
