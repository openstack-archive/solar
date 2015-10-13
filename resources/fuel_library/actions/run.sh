#!/bin/bash

mkdir -p {{temp_directory}}

pushd {{temp_directory}}
if [ ! -d fuel-library ]
then
    git clone -b {{ git['branch'] }} {{ git['repository'] }}
else
    pushd ./fuel-library
    git pull
    popd
fi
pushd ./fuel-library/deployment
./update_modules.sh
popd

mkdir -p {{puppet_modules}}
cp -r ./fuel-library/deployment/puppet/* {{puppet_modules}}
popd
