
Inventory mechanism should provide an easy way for user to change any
piece of deployment configuration.

It means several things:
1. When writing modules - developer should take into account possibility
of modification it by user. Development may take a little bit longer, but we
are developing tool that will cover not single particular use case,
but a broad range customized production deployments.

2. Each resource should define what is changeable.

On the stage before deployment we will be able to know what resources
are used on the level of node/cluster and modify them the way we want.
