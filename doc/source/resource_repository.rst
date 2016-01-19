.. _resource_repository_details:

Resource Repository
===================

Resource Repository takes care about :ref:`resource_details` definitions and it
supports versioning.

Solar CLI supports following options::

  add       Adds new resource to repository
  contains  Checks if `spec` is in Solar repositories
  destroy   Destroys repository
  import    Imports repository to Solar
  remove    Removes `spec` from Solar repositories
  show      Shows all added repositories, or content of repository when `-r`
            given
  update    Updates existing repository with new content



Resource Repository spec
------------------------

`spec` is in format `{repository_name}/{resource_name}:{version_info}`,
`version_info` is optional if omitted, latest (highest) will be used.  Versions
are in `Semantic Versioning <http://semver.org/>` format.
You can also use `>`, `>=`, `==`, `<`, `<=` operators to specify matches.


Resource Repository import
--------------------------

Command `solar repository import` it allows you to import existing repository or
directory with resources into your system. It will traverse `source` path copy
all resources definitions into repository and obviously proper structure will be
automatically created.

.. note::
   You may also check `--link` option to this command. It will just link
   repository contents so to import you need to have proper structure before.


Resource Repository update
--------------------------

Command `solar repository update` will update repository content with new data.
With `--overwrite` flag it will overwrite conflicting resources definitions.
