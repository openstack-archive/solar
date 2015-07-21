# Overview of orchestration commands and system log integration

After user created all required resource - it is possible to automatically
detect which resource requires changes with

```
solar changes stage
```

After changes are staged - they will be used to populate history which can be seen
with command (*n* option used to limit number of items, -1 will return all changes)

```
solar changes history -n 5
```

User is able to generate deployment scenario based on changes found by system log.
```
solar changes process
```

This command will prepare deployment graph, and return uid of deployment graph to
work with.

All commands that are able to manipulate deployment graph located in
*orch* namespace.

Report will print all deployment tasks in topological order, with status,
and error if status of task is *ERROR*
```
solar orch report <uid>
```

To see picture of deployment dependencies one can use following command
```
solar orch dg <uid>
```
Keep in mind that it is not representation of all edges that are kept in graph,
we are using trasitive reduction to leave only edges that are important for the
order of traversal.

Execute deployment
```
solar orch run-once <uid>
```

Gracefully stop deployment, after all already scheduled tasks are finished
```
solar orch stop <uid>
```

Continue deployment execution for all tasks that are SKIPPED
```
solar orch resume <uid>
```

All tasks will be returned to PENDING state, and deployment will be restarted
```
solar orch restart <uid>
```

Orchestrator will retry tasks in ERROR state and continue execution
```
solar orch retry <uid>
```
