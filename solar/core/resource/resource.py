# -*- coding: utf-8 -*-
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

from copy import deepcopy
from hashlib import md5
import itertools
import json
import os
from uuid import uuid4

from enum import Enum
import networkx

from solar.computable_inputs import ComputablePassedTypes
from solar.core.resource.repository import read_meta
from solar.core.resource.repository import Repository
from solar.core.signals import get_mapping
from solar.core.tags_set_parser import Expression
from solar.core.tags_set_parser import get_string_tokens
from solar.core import validation
from solar.dblayer.model import NONE
from solar.dblayer.model import StrInt
from solar.dblayer.solar_models import CommitedResource
from solar.dblayer.solar_models import LogItem
from solar.dblayer.solar_models import Resource as DBResource
from solar.events import api
from solar import utils

"""
created - resource is created by user
operational - set in commit part of system_log
removed - removed by user, will be deleted from database during commit
error - set in commit, if there was errors in task execution
"""
RESOURCE_STATE = Enum(
    'ResourceState', 'created operational removed error')


class Resource(object):
    _metadata = {}

    # Create
    def create_from_spec(self, name, spec, args=None, tags=None):
        args = args or {}
        self.name = name
        if spec:
            if spec.startswith('/'):
                # it's full path, don't use repo
                self.base_path = spec
                metadata = read_meta(spec)
            else:
                repo, spec = Repository.parse(spec)
                metadata = repo.get_metadata(spec)
                self.base_path = repo.get_path(spec)
        else:
            metadata = deepcopy(self._metadata)
            self.base_path = spec  # TODO: remove this old method?

        if tags is None:
            tags = []
        m_tags = metadata.get('tags', [])
        tags.extend(m_tags)
        tags.append('resource={}'.format(name))

        inputs = metadata.get('input', {})

        self.auto_extend_inputs(inputs)
        self.db_obj = DBResource.from_dict(
            name,
            {
                'id': name,
                'name': name,
                'actions_path': metadata.get('actions_path', ''),
                'actions': metadata.get('actions', {}),
                'base_name': metadata.get('base_name', ''),
                'base_path': metadata.get('base_path', ''),
                'handler': metadata.get('handler', ''),
                'version': metadata.get('version', ''),
                'meta_inputs': inputs,
                'tags': tags,
                'state': RESOURCE_STATE.created.name,
                'managers': metadata.get('managers', [])
            })
        self.create_inputs(args)

        self.db_obj.save()
        LogItem.new({
            'resource': self.name,
            'action': 'run',
            'log': 'staged',
            'tags': self.tags}).save_lazy()

    # Load
    def create_from_db(self, resource_db):
        self.db_obj = resource_db
        self.name = resource_db.name
        self.base_path = resource_db.base_path

    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            return self.create_from_db(args[0])
        elif len(args) == 0 and 'resource_db' in kwargs:
            return self.create_from_db(**kwargs)
        args_names = ('name', 'spec', 'args', 'tags')
        for i, arg in enumerate(args):
            kwargs[args_names[i]] = arg
        if isinstance(kwargs[args_names[0]], basestring) and \
           isinstance(kwargs[args_names[1]], basestring):
            return self.create_from_spec(**kwargs)
        raise RuntimeError("Failed to create Resoruce object "
                           "from args: %r and kwargs: %r" % (args, kwargs))

    def auto_extend_inputs(self, inputs):
        # XXX: we didn't agree on `location_id` and `transports_id`
        # that are added automaticaly to all resources
        # using inputs for something like that may be not the best idea
        # maybe we need something like `internal_input`
        inputs.setdefault('location_id', {'value': "",
                                          'schema': 'str!'})
        inputs.setdefault('transports_id', {'value': "",
                                            'schema': 'str'})
        for inp in ('transports_id', 'location_id'):
            if inputs[inp].get('value') == '$uuid':
                inputs[inp]['value'] = md5(self.name + uuid4().hex).hexdigest()

    def transports(self):
        db_obj = self.db_obj
        return db_obj.inputs._get_field_val('transports_id',
                                            other='transports')

    def ip(self):
        db_obj = self.db_obj
        return db_obj.inputs._get_field_val('location_id', other='ip')

    def get_file_path(self, rel_path):
        base_path = self.db_obj.base_path
        path = os.path.join(base_path, rel_path)
        return path

    @property
    def actions(self):
        if self.db_obj.actions:
            return {action: os.path.join(
                self.db_obj.actions_path, name)
                for action, name in self.db_obj.actions.items()}
        # else
        ret = {
            os.path.splitext(p)[0]: os.path.join(
                self.db_obj.actions_path, p
            )
            for p in os.listdir(self.db_obj.actions_path)
        }

        return {
            k: v for k, v in ret.items() if os.path.isfile(v)
        }

    def create_inputs(self, args=None):
        args = args or {}
        for name, v in self.db_obj.meta_inputs.items():
            value = args.get(name, v.get('value'))
            self.db_obj.inputs[name] = value

    @property
    def args(self):
        return self.db_obj.inputs.as_dict()

    def input_add(self, name, value=NONE, schema=None):
        v = self.db_obj.inputs.add_new(name, value, schema)
        self.db_obj.save_lazy()
        return v

    def input_computable_change(self, name, *args, **kwargs):
        if args:
            order = ('func', 'type', 'lang')
            kwargs.update(dict(zip(order, args)))
        kwargs = dict((x, kwargs[x]) for x in kwargs if kwargs[x] is not None)
        db_obj = self.db_obj
        mi = db_obj.meta_inputs
        try:
            computable = mi[name]['computable']
        except KeyError:
            raise Exception("Can't change computable input properties "
                            "when input is not computable.")
        computable.update(kwargs)
        if not isinstance(computable['type'], ComputablePassedTypes):
            type_ = ComputablePassedTypes[computable['type']].name
        else:
            type_ = computable['type'].name
        computable['type'] = type_
        # we don't track nested dicts, only setting full dict will trigger
        # change
        mi[name]['computable'] = computable
        db_obj.meta_inputs = mi
        db_obj.save_lazy()
        return True

    def input_delete(self, name):
        self.db_obj.inputs.remove_existing(name)
        self.db_obj.save_lazy()
        return

    def update(self, args):
        for k, v in args.items():
            self.db_obj.inputs[k] = v
        self.db_obj.save_lazy()
        # created state will be changed during commit
        if self.db_obj.state != RESOURCE_STATE.created.name:
            action = 'update'
        else:
            action = 'run'
        LogItem.new(
            {'resource': self.name,
             'action': action,
             'tags': self.tags}).save_lazy()

    def delete(self):
        return self.db_obj.delete()

    def remove(self, force=False):
        if force:
            self.delete()
        else:
            self.db_obj.state = RESOURCE_STATE.removed.name
            self.db_obj.save_lazy()
            LogItem.new(
                {'resource': self.name,
                 'action': 'remove',
                 'log': 'staged',
                 'tags': self.tags}).save_lazy()

    def set_operational(self):
        self.db_obj.state = RESOURCE_STATE.operational.name
        self.db_obj.save_lazy()

    def set_error(self):
        self.db_obj.state = RESOURCE_STATE.error.name
        self.db_obj.save_lazy()

    def set_created(self):
        self.db_obj.state = RESOURCE_STATE.created.name
        self.db_obj.save_lazy()

    def to_be_removed(self):
        return self.db_obj.state == RESOURCE_STATE.removed.name

    @property
    def tags(self):
        return self.db_obj.tags

    def add_tags(self, *tags):
        for tag in tags:
            self.db_obj.tags.set(tag)
        self.db_obj.save_lazy()

    def remove_tags(self, *tags):
        for tag in tags:
            self.db_obj.tags.remove(tag)
        self.db_obj.save_lazy()

    @property
    def connections(self):
        """Gives you all incoming/outgoing connections for current resource.

        Stored as:
        [(emitter, emitter_input, receiver, receiver_input), ...]
        """
        rst = set()
        for (emitter_resource, emitter_input), (receiver_resource, receiver_input), meta in self.graph().edges(data=True):  # NOQA
            if meta:
                receiver_input = '{}:{}|{}'.format(receiver_input,
                                                   meta['destination_key'],
                                                   meta['tag'])

            rst.add(
                (emitter_resource, emitter_input,
                 receiver_resource, receiver_input))
        return [list(i) for i in rst]

    def graph(self):
        mdg = networkx.MultiDiGraph()
        for u, v, data in self.db_obj.inputs._edges():
            mdg.add_edge(u, v, attr_dict=data)
        return mdg

    def resource_inputs(self):
        return self.db_obj.inputs

    def to_dict(self, inputs=False):
        ret = self.db_obj.to_dict()
        if inputs:
            ret['inputs'] = self.db_obj.inputs.as_dict()
        return ret

    def color_repr(self, inputs=False):
        import click

        arg_color = 'yellow'

        return ("{resource_s}({name_s}='{key}', {base_path_s}={base_path} "
                "{args_s}={inputs}, {tags_s}={tags})").format(
            resource_s=click.style('Resource', fg='white', bold=True),
            name_s=click.style('name', fg=arg_color, bold=True),
            base_path_s=click.style('base_path', fg=arg_color, bold=True),
            args_s=click.style('args', fg=arg_color, bold=True),
            tags_s=click.style('tags', fg=arg_color, bold=True),
            **self.to_dict(inputs)
        )

    def load_commited(self):
        return CommitedResource.get_or_create(self.name)

    def _connect_inputs(self, receiver, mapping):
        if isinstance(mapping, set):
            mapping = dict((x, x) for x in mapping)
        self.db_obj.connect(receiver.db_obj, mapping=mapping)
        self.db_obj.save_lazy()
        receiver.db_obj.save_lazy()

    def connect_with_events(self, receiver, mapping=None, events=None,
                            use_defaults=False):
        mapping = get_mapping(self, receiver, mapping)
        self._connect_inputs(receiver, mapping)
        LogItem.new({'resource': receiver.name,
                     'action': 'run',
                     'tags': receiver.tags}).save_lazy()
        # signals.connect(self, receiver, mapping=mapping)
        # TODO: implement events
        if use_defaults:
            if self != receiver:
                api.add_default_events(self, receiver)
        if events:
            api.add_events(self.name, events)

    def connect(self, receiver, mapping=None, events=None):
        return self.connect_with_events(
            receiver, mapping=mapping, events=events, use_defaults=True)

    def disconnect(self, receiver):
        inputs = self.db_obj.inputs.keys()
        self.db_obj.disconnect(other=receiver.db_obj, inputs=inputs)
        receiver.db_obj.save_lazy()
        self.db_obj.save_lazy()

    def prefetch(self):
        if not self.db_obj.managers:
            return

        for manager in self.db_obj.managers:
            manager_path = os.path.join(self.db_obj.base_path, manager)
            rst = utils.communicate([manager_path], json.dumps(self.args))
            if rst:
                self.update(json.loads(rst))


def load(name):
    r = DBResource.get(name)

    if not r:
        raise Exception('Resource {} does not exist in DB'.format(name))

    return Resource(r)


def load_childs(parents):
    return [Resource(r) for r in
            DBResource.multi_get(DBResource.childs(parents))]


def load_all(startswith=None):
    if startswith:
        start = startswith
        end = startswith + '~'
        candids = DBResource.bucket.get_index("$key", start, end).results
    else:
        candids = DBResource.updated.filter(StrInt.p_min(), StrInt.p_max())
    return [Resource(r) for r in DBResource.multi_get(candids)]


def load_by_tags(query):
    if isinstance(query, (list, set, tuple)):
        query = '|'.join(query)

    parsed_tags = get_string_tokens(query)
    r_with_tags = [DBResource.tags.filter(tag) for tag in parsed_tags]
    r_with_tags = set(itertools.chain(*r_with_tags))
    resources = [Resource(r) for r in DBResource.multi_get(r_with_tags)]

    return filter(lambda n: Expression(query, n.tags).evaluate(), resources)


def stage_resources(resources_query, action):
    """Create log items for resources selected by query
    :param resources_query: iterable with tags or basestring
    :param action: basestring
    """
    if isinstance(resources_query, basestring):
        resources = [load(resources_query)]
    else:
        resources = load_by_tags(resources_query)
    created = []
    for resource in resources:
        # save - cache doesnt cover all query in the same sesssion
        # and this query will be triggered right after staging resources

        log_item = LogItem.new(
            {'resource': resource.name,
             'action': action,
             'log': 'staged',
             'tags': resource.tags})
        log_item.save()
        created.append(log_item)
    return created


def load_by_names(names):
    return [Resource(r) for r in DBResource.multi_get(names)]


def validate_resources():
    resources = load_all()

    ret = []

    for r in resources:
        e = validation.validate_resource(r)
        if e:
            ret.append((r, e))

    return ret
