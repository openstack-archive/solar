#!/bin/sh -eux
# Remove Linux headers
yum -y remove gcc kernel-devel kernel-headers
yum -y clean all

# Remove Virtualbox specific files
rm -rf /usr/src/vboxguest* /usr/src/virtualbox-ose-guest*
rm -rf *.iso *.iso.? /tmp/vbox /home/vagrant/.vbox_version

# Cleanup log files
find /var/log -type f | while read f; do echo -ne '' > $f; done;

rm -rf /usr/share/doc/*

# remove interface persistent
rm -f /etc/udev/rules.d/70-persistent-net.rules

for ifcfg in $(ls /etc/sysconfig/network-scripts/ifcfg-*)
do
    bn=$(basename ${ifcfg})
    if [ "${bn}" != "ifcfg-lo" ]
    then
        sed -i '/^UUID/d'   /etc/sysconfig/network-scripts/${bn}
        sed -i '/^HWADDR/d' /etc/sysconfig/network-scripts/${bn}
    fi
done

dd if=/dev/zero of=/EMPTY bs=1M
rm -f /EMPTY

# Make sure we wait until all the data is written to disk, otherwise
# Packer might quite too early before the large files are deleted
sync
