#!/bin/bash
set -eux

function deploy {
    # this two commands will clean db
    solar resource clear_all
    solar connections clear_all

    solar resource create node1 /vagrant/resources/ro_node ip=10.0.0.3 ssh_user=vagrant ssh_key='/vagrant/.vagrant/machines/solar-dev1/virtualbox/private_key'
    solar resource create mariadb1 /vagrant/resources/mariadb_service image=mariadb port=3306
    solar connect node1 mariadb1

    solar changes stage
    solar changes process
    solar orch run-once last
    solar orch report last
}

deploy
