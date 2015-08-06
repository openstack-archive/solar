#!/bin/sh

apt-get remove -f python-pip
sudo apt-get install -y python-setuptools
sudo easy_install pip
sudo pip install -U pip
sudo pip install ansible
