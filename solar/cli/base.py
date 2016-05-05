#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from functools import wraps

import click

from solar.dblayer.model import DBLayerException
from solar.errors import SolarError


class AliasedGroup(click.Group):
    """This class introduces iproute2-like behaviour,

    command will be inferredby matching patterns.
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


class BaseGroup(click.Group):
    error_wrapper_enabled = False

    def add_command(self, cmd, name=None):
        cmd.callback = self.error_wrapper(cmd.callback)
        return super(BaseGroup, self).add_command(cmd, name)

    def error_wrapper(self, f):
        @wraps(f)
        def _in(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except (SolarError, DBLayerException) as e:
                self.handle_exception(e)
                if self.error_wrapper_enabled:
                    raise click.ClickException(str(e))
                raise
            except Exception as e:
                self.handle_exception(e)
                raise
        return _in

    def handle_exception(self, e):
        pass
