# TODO

- grammar connections fuzzy matching algorithm (for example: type 'login' joins to type 'login' irrespective of names of both inputs)
- resource connections JS frontend (?)
- store all resource configurations somewhere globally (this is required to
  correctly perform an update on one resource and bubble down to all others)
- config templates
- Handler also can require some data, for example ansible:  ip, ssh_key, ssh_user 
- tag-filtered graph generation
- separate resource for docker image -- this is e.g. to make automatic image removal
  when some image is unused to conserve space

# DONE
- CI
- Deploy HAProxy, Keystone and MariaDB
- ansible handler (loles)
- tags are kept in resource mata file (pkaminski)
- add 'list' connection type (pkaminski)
- connections are made automaticly(pkaminski)
- graph is build from CLIENT dict, clients are stored in JSON file (pkaminski)
- cli (pkaminski)
