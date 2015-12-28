#!/bin/bash
set -eux

function deploy {
    # this two commands will clean db
    solar resource clear_all

    solar resource create nodes templates/nodes '{"count": 1}'
    solar resource create mariadb1 /vagrant/resources/mariadb_service image=mariadb port=3306
    solar connect node1 mariadb1

    solar changes stage
    solar changes process
    solar orch run-once last
    solar orch report last
}

deploy
