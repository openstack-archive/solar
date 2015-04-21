# TODO

- store all resource configurations somewhere globally (this is required to
  correctly perform an update on one resource and bubble down to all others)
- ansible handler (loles)
- config templates
- Deploy HAProxy, Keystone and MariaDB
- Handler also can require some data, for example ansible:  ip, ssh_key, ssh_user 
- tag-filtered graph generation
- separate resource for docker image -- this is e.g. to make automatic image removal
  when some image is unused to conserve space

# DONE
- tags are kept in resource mata file (pkaminski)
- add 'list' connection type (pkaminski)
- connections are made automaticly(pkaminski)
- graph is build from CLIENT dict, clients are stored in JSON file (pkaminski)
- cli (pkaminski)
