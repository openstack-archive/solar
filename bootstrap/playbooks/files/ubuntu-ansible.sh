#!/bin/sh

# TODO: maybe this is better:
# http://docs.ansible.com/ansible/intro_installation.html#latest-releases-via-apt-ubuntu

apt-get remove -f python-pip
sudo apt-get install -y python-setuptools
sudo easy_install pip
sudo pip install -U pip
sudo pip install ansible
