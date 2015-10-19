#!/bin/bash

set -eux

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

solar resource clear_all
python "${DIR}"/provision.py

solar changes stage
solar changes process
solar orch run-once last
watch --color -n1 'solar orch report last'

