#!/bin/bash

set -eux

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Remove generated pxe exclude files
sudo rm -f /etc/dnsmasq.d/no_pxe_*.conf
sudo service dnsmasq restart

solar resource clear_all
python "${DIR}"/provision.py

solar changes stage
solar changes process
solar orch run-once last
watch --color -n1 'solar orch report last'
