#! /bin/bash

vagrant up
vagrant ssh -c /vagrant/utils/k8s/deploy.sh
