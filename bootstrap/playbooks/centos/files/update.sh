#!/bin/bash -eux

if [[ $UPDATE  =~ true || $UPDATE =~ 1 || $UPDATE =~ yes ]]; then
  	echo "==> Updating non kernel packages"
    yum --exclude=kernel* update
    echo "==> Upgrading all"
    yum upgrade yum kernel
    yum -y upgrade
    reboot
    sleep 160
fi
