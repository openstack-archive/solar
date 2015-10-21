#!/bin/bash

set -eux
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# TODO should be a way to render configs, in order to do this
# we should have scripts dir variable passed from above
sed -i "s|<ROOT>|${DIR}|" "${DIR}"/templates/agent.config
provision --input_data_file "${DIR}"/templates/provisioning.json --config-file "${DIR}"/templates/agent.config
