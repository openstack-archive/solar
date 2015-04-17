#!/bin/bash

docker exec -it keystone-test keystone --debug --os-username admin --os-password password --os-tenant-name admin --os-auth-url http://10.0.0.3:8080/v2.0 role-list
