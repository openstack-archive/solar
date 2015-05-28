#!/bin/bash

export OS_SERVICE_TOKEN=admin
export OS_SERVICE_ENDPOINT=http://localhost:35357/v2.0

keystone tenant-create --name=service_admins
keystone user-create --name=glance_admin --password=passsword1234
keystone role-create --name=service_role
keystone user-role-add --user=glance_admin --tenant=service_admins --role=service_role
