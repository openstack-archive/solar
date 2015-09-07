

import click


class AliasedGroup(click.Group):
    """This class introduces iproute2-like behaviour, command will be inferred
    by matching patterns.
    If there will be more than 1 matches - exception will be raised

    Examples:
    >> solar ch stage
    >> solar cha process
    >> solar res action run rabbitmq_service1
    """
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))