"""

task should be visited only when predecessors are visited,
visited node could be only in SUCCESS or ERROR

task can be scheduled for execution if it is not yet visited, and state
not in SKIPPED, INPROGRESS

PENDING - task that is scheduled to be executed
ERROR - visited node, but failed, can be failed by timeout
SUCCESS - visited node, successfull
INPROGRESS - task already scheduled, can be moved to ERROR or SUCCESS
SKIPPED - not visited, and should be skipped from execution
NOOP - task wont be executed, but should be treated as visited
"""


VISITED = ('SUCCESS', 'ERROR', 'NOOP')
BLOCKED = ('INPROGRESS', 'SKIPPED')


def traverse(dg):

    visited = set()
    for node in dg:
        data = dg.node[node]
        if data['status'] in VISITED:
            visited.add(node)

    for node in dg:
        data = dg.node[node]

        if node in visited or data['status'] in BLOCKED:
            continue

        if set(dg.predecessors(node)) <= visited:
            yield node
