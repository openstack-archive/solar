#!/bin/sh

# TODO: maybe this is better:
# http://docs.ansible.com/ansible/intro_installation.html#latest-releases-via-apt-ubuntu

sudo apt-get remove -f python-pip
sudo apt-get update
sudo apt-get install -y python-setuptools python-dev autoconf g++
sudo easy_install pip
sudo pip install -U pip
sudo pip install "ansible<2.0"
