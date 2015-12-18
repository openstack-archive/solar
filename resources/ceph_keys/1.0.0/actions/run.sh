#!/bin/sh

BASE_PATH={{ target_directory }}
KEY_NAME={{ key_name }}

function generate_ssh_keys {
    local dir_path=$BASE_PATH$KEY_NAME/
    local key_path=$dir_path$KEY_NAME
    mkdir -p $dir_path
    if [ ! -f $key_path ]; then
      ssh-keygen -b 2048 -t rsa -N '' -f $key_path 2>&1
    else
      echo 'Key $key_path already exists'
    fi
}

generate_ssh_keys
