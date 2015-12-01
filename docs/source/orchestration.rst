.. _orchestration:

Deployment operations
=====================

Stage changes
-------------

After user created all required resource - it is possible to automatically
detect which resource requires changes with ::

    solar changes stage


History
-------
After changes are staged - they will be used to populate history which can be seen
with command (*n* option used to limit number of items, -1 will return all changes) ::

    solar changes history -n 5

Prepare deployment plan
-----------------------

User is able to generate deployment scenario based on changes found by system log. ::

    solar changes process


This command will prepare deployment graph, and return uid of deployment graph to
work with.

All commands that are able to manipulate deployment graph located in
*orch* namespace.


.. tip::
   Solar writes returned deployment graph uid into special file (`.solar_cli_uids`), it
   allows you to use `last` instead of full returned uid:
   `solar orch report <uid>` becomes `solar orch report last`


Report
------
Report will print all deployment tasks in topological order, with status,
and error if status of task is *ERROR* ::

    solar orch report <uid>

Graphviz graph
--------------
To see picture of deployment dependencies one can use following command ::

    solar orch dg <uid>

Keep in mind that it is not representation of all edges that are kept in graph,
we are using trasitive reduction to leave only edges that are important for the
order of traversal.

Run deployment
--------------
Execute deployment ::

    solar orch run-once <uid>


Stop deployment
---------------
Gracefully stop deployment, after all already scheduled tasks are finished ::

    solar orch stop <uid>

Resume deployment
-----------------
Reset SKIPPED tasks to PENDING and continue deployment ::

    solar orch resume <uid>

Restart deployment
------------------
All tasks will be returned to PENDING state, and deployment will be restarted ::

    solar orch restart <uid>

Retry deployment
----------------
Orchestrator will reset all ERROR tasks to PENDING state and restart deployment ::

    solar orch retry <uid>
