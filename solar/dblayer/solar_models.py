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


from collections import defaultdict
from itertools import chain
from operator import itemgetter
from types import NoneType
from uuid import uuid4

from enum import Enum

from solar.computable_inputs import ComputablePassedTypes
from solar.computable_inputs.processor import get_processor
from solar.config import C
from solar.dblayer.model import check_state_for
from solar.dblayer.model import CompositeIndexField
from solar.dblayer.model import DBLayerException
from solar.dblayer.model import Field
from solar.dblayer.model import IndexedField
from solar.dblayer.model import IndexField
from solar.dblayer.model import IndexFieldWrp
from solar.dblayer.model import Model
from solar.dblayer.model import NONE
from solar.dblayer.model import SingleIndexCache
from solar.dblayer.model import StrInt
from solar.utils import detect_input_schema_by_value
from solar.utils import parse_database_conn
from solar.utils import solar_map


InputTypes = Enum('InputTypes', 'simple list hash list_hash computable')


class DBLayerSolarException(DBLayerException):
    pass


class UnknownInput(DBLayerSolarException, KeyError):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Unknown input %s" % self.name


class InputAlreadyExists(DBLayerSolarException):
    pass


class InputsFieldWrp(IndexFieldWrp):

    _simple_types = (NoneType, int, float, basestring, str, unicode)

    def __init__(self, *args, **kwargs):
        super(InputsFieldWrp, self).__init__(*args, **kwargs)
        # TODO: add cache for lookup
        self.inputs_index_cache = SingleIndexCache()
        self._cache = {}

    def _input_type(self, resource, name):
        # XXX: it could be worth to precalculate it
        if ':' in name:
            name = name.split(":", 1)[0]
        mi = resource.meta_inputs[name]
        schema = mi.get('schema', None)
        is_computable = mi.get('computable', None) is not None
        if is_computable:
            return InputTypes.computable
        if isinstance(schema, self._simple_types):
            return InputTypes.simple
        if isinstance(schema, list):
            if len(schema) > 0 and isinstance(schema[0], dict):
                return InputTypes.list_hash
            return InputTypes.list
        if isinstance(schema, dict):
            return InputTypes.hash
        raise Exception("Unknown type")

    def _edges_fmt(self, vals):
        for val in vals:
            data = val.split('|')
            dlen = len(data)
            my_resource = data[0]
            my_input = data[1]
            other_resource = data[2]
            other_input = data[3]
            if dlen == 5:
                meta = None
            elif dlen == 7:
                meta = {'destination_key': data[5], 'tag': data[4]}
            else:
                raise Exception("Unsupported case")
            yield (other_resource, other_input), (my_resource, my_input), meta

    def _edges(self):
        inst = self._instance
        start = inst.key
        my_ind_name = '{}_recv_bin'.format(self.fname)
        res = inst._get_index(my_ind_name,
                              startkey=start + '|',
                              endkey=start + '|~',
                              return_terms=True,
                              max_results=99999).results
        vals = map(itemgetter(0), res)
        return self._edges_fmt(vals)

    def _single_edge(self, name):
        inst = self._instance
        self._has_own_input(name)
        start = '{}|{}'.format(inst.key, name)
        my_ind_name = '{}_recv_bin'.format(self.fname)
        res = inst._get_index(my_ind_name,
                              startkey=start + '|',
                              endkey=start + '|~',
                              return_terms=True,
                              max_results=99999).results
        vals = map(itemgetter(0), res)
        return self._edges_fmt(vals)

    def __contains__(self, name):
        try:
            self._has_own_input(name)
        except Exception:
            return False
        else:
            return True

    def __iter__(self):
        for name in self._instance._data_container[self.fname]:
            yield name

    def keys(self):
        return list(self.__iter__())

    def as_dict(self):
        items = solar_map(lambda x: (x, self._get_field_val(x)),
                          [x for x in self],
                          concurrency=3)
        return dict(items)

    def _connect_my_simple(self, my_resource, my_inp_name, other_resource,
                           other_inp_name, my_type, other_type):
        types_mapping = '|{}_{}'.format(my_type.value, other_type.value)
        my_ind_name = '{}_recv_bin'.format(self.fname)
        my_ind_val = '{}|{}|{}|{}'.format(my_resource.key, my_inp_name,
                                          other_resource.key, other_inp_name)
        my_ind_val += types_mapping

        real_my_type = self._input_type(my_resource, my_inp_name)
        if real_my_type == InputTypes.simple:
            for ind_name, ind_value in my_resource._riak_object.indexes:
                if ind_name == my_ind_name:
                    mr, mn, _ = ind_value.split('|', 2)
                    if mr == my_resource.key and mn == my_inp_name:
                        my_resource._remove_index(ind_name, ind_value)
                        break

        my_resource._add_index(my_ind_name, my_ind_val)
        return my_inp_name

    def _connect_other_simple(self, my_resource, my_inp_name, other_resource,
                              other_inp_name, my_type, other_type):
        other_ind_name = '{}_emit_bin'.format(self.fname)

        real_my_type = self._input_type(my_resource, my_inp_name)
        if real_my_type == InputTypes.simple or ':' not in my_inp_name:
            other_ind_val = '{}|{}|{}|{}'.format(other_resource.key,
                                                 other_inp_name,
                                                 my_resource.key, my_inp_name)
            for ind_name, ind_value in my_resource._riak_object.indexes:
                if ind_name == other_ind_name:
                    try:
                        mr, mn = ind_value.rsplit('|')[2:]
                    except ValueError:
                        if len(ind_value.split('|')) == 6:
                            continue
                        else:
                            raise
                    if mr == my_resource.key and mn == my_inp_name:
                        my_resource._remove_index(ind_name, ind_value)
                        break

        elif real_my_type in (InputTypes.list_hash, InputTypes.hash,
                              InputTypes.list):
            my_key, my_val = my_inp_name.split(':', 1)
            if '|' in my_val:
                my_val, my_tag = my_val.split('|', 1)
            else:
                if real_my_type == InputTypes.hash:
                    # when single dict then set shared hash for all resources
                    # TODO: (jnowak) maybe we should remove tags completely
                    # in this and only this case
                    my_tag = '_single'
                else:
                    my_tag = other_resource.name
            my_inp_name = my_key
            other_ind_val = '{}|{}|{}|{}|{}|{}'.format(
                other_resource.key, other_inp_name, my_resource.key,
                my_inp_name, my_tag, my_val)
            for ind_name, ind_value in my_resource._riak_object.indexes:
                if ind_name == other_ind_name:
                    try:
                        mr, mn, mt, mv = ind_value.rsplit('|')[2:]
                    except ValueError:
                        if len(ind_value.split('|')) == 4:
                            continue
                        else:
                            raise
                    if mr == my_resource.key and mn == my_inp_name \
                       and mt == my_tag and mv == my_val:
                        my_resource._remove_index(ind_name, ind_value)
                        break
        else:
            raise Exception("Unsupported connection type")
        my_resource._add_index(other_ind_name, other_ind_val)
        return other_inp_name

    def _connect_other_hash(self, my_resource, my_inp_name, other_resource,
                            other_inp_name, my_type, other_type):
        return self._connect_other_simple(
            my_resource, my_inp_name, other_resource, other_inp_name, my_type,
            other_type)

    def _connect_other_list(self, my_resource, my_inp_name, other_resource,
                            other_inp_name, my_type, other_type):
        return self._connect_other_simple(
            my_resource, my_inp_name, other_resource, other_inp_name, my_type,
            other_type)

    def _connect_other_list_hash(self, my_resource, my_inp_name,
                                 other_resource, other_inp_name, my_type,
                                 other_type):
        return self._connect_other_simple(
            my_resource, my_inp_name, other_resource, other_inp_name, my_type,
            other_type)

    def _connect_other_computable(self, my_resource, my_inp_name,
                                  other_resource, other_inp_name, my_type,
                                  other_type):
        return self._connect_other_simple(
            my_resource, my_inp_name, other_resource, other_inp_name, my_type,
            other_type)

    def _connect_my_list(self, my_resource, my_inp_name, other_resource,
                         other_inp_name, my_type, other_type):
        ret = self._connect_my_simple(my_resource, my_inp_name, other_resource,
                                      other_inp_name, my_type, other_type)
        return ret

    def _connect_my_hash(self, my_resource, my_inp_name, other_resource,
                         other_inp_name, my_type, other_type):

        my_key, my_val = my_inp_name.split(':', 1)
        if '|' in my_val:
            my_val, my_tag = my_val.split('|', 1)
        else:
            # when single dict then set shared hash for all resources
            # TODO: (jnowak) maybe we should remove tags completely there
            if my_type == InputTypes.hash:
                my_tag = '_single'
            else:
                my_tag = other_resource.name
        types_mapping = '|{}_{}'.format(my_type.value, other_type.value)
        my_ind_name = '{}_recv_bin'.format(self.fname)
        my_ind_val = '{}|{}|{}|{}|{}|{}'.format(my_resource.key, my_key,
                                                other_resource.key,
                                                other_inp_name, my_tag, my_val)
        my_ind_val += types_mapping

        my_resource._add_index(my_ind_name, my_ind_val)
        return my_key

    def _connect_my_list_hash(self, my_resource, my_inp_name, other_resource,
                              other_inp_name, my_type, other_type):
        return self._connect_my_hash(my_resource, my_inp_name, other_resource,
                                     other_inp_name, my_type, other_type)

    def _connect_my_computable(self, my_resource, my_inp_name, other_resource,
                               other_inp_name, my_type, other_type):
        return self._connect_my_simple(my_resource, my_inp_name,
                                       other_resource, other_inp_name,
                                       my_type, other_type)

    def connect(self, my_inp_name, other_resource, other_inp_name):
        my_resource = self._instance
        other_type = self._input_type(other_resource, other_inp_name)
        my_type = self._input_type(my_resource, my_inp_name)

        if my_type == other_type and ':' not in my_inp_name:
            # if the type is the same map 1:1, and flat
            my_type = InputTypes.simple
            other_type = InputTypes.simple
        elif my_type == InputTypes.list_hash and other_type == InputTypes.hash:
            # whole dict to list with dicts
            # TODO: solve this problem
            if ':' in my_inp_name:
                my_type = InputTypes.hash
            else:
                my_type = InputTypes.list

        # set my side
        my_meth = getattr(self, '_connect_my_{}'.format(my_type.name))
        my_affected = my_meth(my_resource, my_inp_name, other_resource,
                              other_inp_name, my_type, other_type)

        # set other side
        other_meth = getattr(self, '_connect_other_{}'.format(other_type.name))
        other_meth(my_resource, my_inp_name, other_resource, other_inp_name,
                   my_type, other_type)

        try:
            del self._cache[my_affected]
        except KeyError:
            pass

        with self.inputs_index_cache as c:
            c.wipe()

        return True

    def disconnect(self, name):
        # ind_name  = '{}_recv_bin'.format(self.fname)
        if ':' in name:
            # disconnect from hash with tag
            normalized_name, tag_and_target = name.split(':', 1)
            my_val, my_tag = tag_and_target.split('|', 1)
            emit_name = None
            # emit_name = '{}|{}'.format(my_tag, my_val)
            full_name = '{}|{}|{}'.format(normalized_name, my_tag, my_val)
            name = normalized_name
        elif '|' in name:
            # disconnect everything from given input|resource
            my_input, other_resource, other_input = name.split('|', 2)
            full_name = my_input
            emit_name = '{}|{}'.format(other_resource, other_input)
            normalized_name = "{}|{}".format(my_input, other_resource)
            name = name.split('|', 1)[0]
            my_val, my_tag = None, None
        else:
            # disconnect everything from given input
            full_name = name
            emit_name = None
            normalized_name = name
            my_val, my_tag = None, None
        indexes = self._instance._riak_object.indexes
        to_dels = []
        recvs = filter(lambda x: x[0] == '{}_recv_bin'.format(self.fname),
                       indexes)
        for recv in recvs:
            _, ind_value = recv
            if ind_value.startswith('{}|{}|'.format(self._instance.key,
                                                    normalized_name)):
                spl = ind_value.split('|')
                if len(spl) == 7 and my_tag and my_val:
                    if spl[-3] == my_tag and spl[-2] == my_val:
                        to_dels.append(recv)
                else:
                    to_dels.append(recv)
        emits = filter(lambda x: x[0] == '{}_emit_bin'.format(self.fname),
                       indexes)
        for emit in emits:
            _, ind_value = emit
            if ind_value.endswith('|{}|{}'.format(self._instance.key,
                                                  full_name)):
                if emit_name:
                    if ind_value.startswith(emit_name):
                        to_dels.append(emit)
                else:
                    to_dels.append(emit)

        for to_del in to_dels:
            self._instance._remove_index(*to_del)

        try:
            del self._cache[name]
        except KeyError:
            pass

        with self.inputs_index_cache as c:
            c.wipe()

    def _has_own_input(self, name):
        try:
            return self._cache[name]
        except KeyError:
            pass
        my_name = self._instance.key
        try:
            self._get_raw_field_val(name)
        except KeyError:
            raise DBLayerSolarException('No input {} for {}'.format(name,
                                                                    my_name))
        else:
            return True

    def _get_field_val(self, name, other=None):
        # maybe it should be tco
        if other:
            full_name = '{}_other_{}'.format(name, other)
        else:
            full_name = name
        try:
            return self._cache[full_name]
        except KeyError:
            pass
        with self.inputs_index_cache as c:
            check_state_for('index', self._instance)
            fname = self.fname
            my_name = self._instance.key
            self._has_own_input(name)
            ind_name = '{}_recv_bin'.format(fname)
            kwargs = dict(startkey='{}|'.format(my_name),
                          endkey='{}|~'.format(my_name),
                          return_terms=True)
            my_type = self._input_type(self._instance, name)
            if my_type == InputTypes.simple:
                max_results = 1
            else:
                max_results = 99999
            c.get_index(self._instance._get_index, ind_name, **kwargs)
            recvs = tuple(c.filter(startkey="{}|{}|".format(my_name, name),
                                   endkey="{}|{}|~".format(my_name, name),
                                   max_results=max_results))
        if not recvs:
            _res = self._get_raw_field_val(name)
            self._cache[name] = _res
            if other:
                other_res = self._get_field_val(other)
                self._cache[full_name] = other_res
                return other_res
            return _res
        my_meth = getattr(self, '_map_field_val_{}'.format(my_type.name))
        return my_meth(recvs, name, my_name, other=other)

    def _map_field_val_simple(self, recvs, input_name, name, other=None):
        recvs = recvs[0]
        index_val, obj_key = recvs
        _, inp, emitter_key, emitter_inp, _mapping_type = index_val.split('|',
                                                                          4)
        res = Resource.get(emitter_key).inputs._get_field_val(emitter_inp,
                                                              other)
        self._cache[name] = res
        return res

    def _map_field_val_list(self, recvs, input_name, name, other=None):
        if len(recvs) == 1:
            recv = recvs[0]
            index_val, obj_key = recv
            _, inp, emitter_key, emitter_inp, mapping_type = index_val.split(
                '|', 4)
            res = Resource.get(emitter_key).inputs._get_field_val(emitter_inp,
                                                                  other)
            if mapping_type != "{}_{}".format(InputTypes.simple.value,
                                              InputTypes.simple.value):
                res = [res]
        else:
            res = []
            for recv in recvs:
                index_val, obj_key = recv
                _, _, emitter_key, emitter_inp, mapping_type = index_val.split(
                    '|', 4)
                cres = Resource.get(emitter_key).inputs._get_field_val(
                    emitter_inp, other)
                res.append(cres)
        self._cache[name] = res
        return res

    def _map_field_val_hash_single(self, recvs, input_name, other):
        items = []
        tags = set()
        for recv in recvs:
            index_val, obj_key = recv
            (_, _, emitter_key, emitter_inp,
             my_tag, my_val, mapping_type) = index_val.split('|', 6)
            cres = Resource.get(emitter_key).inputs._get_field_val(emitter_inp,
                                                                   other)
            items.append((my_tag, my_val, cres))
            tags.add(my_tag)
        return items, tags

    def _map_field_val_hash(self, recvs, input_name, name, other=None):
        if len(recvs) == 1:
            # just one connected
            recv = recvs[0]
            index_val, obj_key = recv
            splitted = index_val.split('|')
            splen = len(splitted)
            if splen == 5:
                # 1:1
                _, inp, emitter_key, emitter_inp, mapping_type = splitted
                if mapping_type != "{}_{}".format(InputTypes.simple.value,
                                                  InputTypes.simple.value):
                    raise NotImplementedError()
                res = Resource.get(emitter_key).inputs._get_field_val(
                    emitter_inp, other)
            elif splen == 7:
                # partial
                res = {}
                my_resource = self._instance
                my_resource_value = my_resource.inputs._get_raw_field_val(
                    input_name)
                if my_resource_value:
                    for my_val, cres in my_resource_value.iteritems():
                        res[my_val] = cres
                (_, _, emitter_key, emitter_inp,
                 my_tag, my_val, mapping_type) = splitted
                cres = Resource.get(emitter_key).inputs._get_field_val(
                    emitter_inp, other)
                res[my_val] = cres
            else:
                raise Exception("Not supported splen %s", splen)
        else:
            items, tags = self._map_field_val_hash_single(recvs, input_name,
                                                          other)
            my_resource = self._instance
            my_resource_value = my_resource.inputs._get_raw_field_val(
                input_name)
            if my_resource_value:
                res = my_resource_value
            else:
                res = {}
            if len(tags) != 1:
                # TODO: add it also for during connecting
                raise Exception("Detected dict with different tags")
            for _, my_val, value in items:
                res[my_val] = value
        self._cache[name] = res
        return res

    def _map_field_val_list_hash(self, recvs, input_name, name, other=None):
        items = []
        for recv in recvs:
            index_val, obj_key = recv
            splitted_val = index_val.split('|', 6)
            if len(splitted_val) == 5:
                # it was list hash but with whole dict mapping
                _, _, emitter_key, emitter_inp, mapping_type = splitted_val
                cres = Resource.get(emitter_key).inputs._get_field_val(
                    emitter_inp, other)
                items.append((emitter_key, None, cres))
            else:
                (_, _, emitter_key, emitter_inp,
                 my_tag, my_val, mapping_type) = splitted_val
                cres = Resource.get(emitter_key).inputs._get_field_val(
                    emitter_inp, other)
                items.append((my_tag, my_val, cres))
        tmp_res = {}
        for first, my_val, value in items:
            if my_val is None:
                tmp_res[first] = value
            else:
                try:
                    tmp_res[first][my_val] = value
                except KeyError:
                    tmp_res[first] = {my_val: value}
        res = tmp_res.values()
        self._cache[name] = res
        return res

    def _map_field_val_computable(self, recvs, input_name, name, other=None):
        to_calc = []
        computable = self._instance.meta_inputs[input_name]['computable']
        computable_type = computable.get('type',
                                         ComputablePassedTypes.values.name)
        for recv in recvs:
            index_val, obj_key = recv
            splitted = index_val.split('|', 4)
            _, inp, emitter_key, emitter_inp, _ = splitted
            res = Resource.get(emitter_key)
            inp_value = res.inputs._get_field_val(emitter_inp,
                                                  other)
            if computable_type == ComputablePassedTypes.values.name:
                to_calc.append(inp_value)
            else:
                to_calc.append({'value': inp_value,
                                'resource': res.name,
                                'other_input': emitter_inp})
        return get_processor(self._instance, input_name,
                             computable_type, to_calc, other)

    def _get_raw_field_val(self, name):
        return self._instance._data_container[self.fname][name]

    def __getitem__(self, name):
        try:
            return self._get_field_val(name)
        except KeyError:
            raise UnknownInput(name)

    def __delitem__(self, name):
        # TODO: check if something is connected to it
        self._has_own_input(name)
        self._instance._field_changed(self)
        try:
            del self._cache[name]
        except KeyError:
            pass
        inst = self._instance
        inst._riak_object.remove_index('%s_bin' % self.fname, '{}|{}'.format(
            self._instance.key, name))
        del inst._data_container[self.fname][name]

    def __setitem__(self, name, value):
        try:
            mi = self._instance.meta_inputs
        except KeyError:
            pass
        else:
            if name not in mi:
                raise UnknownInput(name)
        self._instance._field_changed(self)
        return self._set_field_value(name, value)

    def items(self):
        return self._instance._data_container[self.fname].items()

    def get(self, name, default=None):
        if self._has_own_input(name):
            return self[name]
        else:
            return default

    def _set_field_value(self, name, value):
        fname = self.fname
        my_name = self._instance.key
        ind_name = '{}_recv_bin'.format(fname)
        recvs = self._instance._get_index(
            ind_name,
            startkey='{}|{}|'.format(my_name, name),
            endkey='{}|{}|~'.format(my_name, name),
            max_results=1,
            return_terms=True).results
        if recvs:
            recvs = recvs[0]
            res, inp, emitter_name, emitter_inp = recvs[0].split('|')[:4]
            raise Exception("%s:%s is connected with resource %s:%s" %
                            (res, inp, emitter_name, emitter_inp))
        # inst = self._instance
        robj = self._instance._riak_object
        if name not in robj.data[self.fname]:
            self._instance._add_index('%s_bin' % self.fname, '{}|{}'.format(
                my_name, name))
        robj.data[self.fname][name] = value

        with self.inputs_index_cache as c:
            c.wipe()
        self._cache[name] = value
        return True

    def to_dict(self):
        rst = {}
        for key in self._instance._data_container[self.fname].keys():
            rst[key] = self[key]
        return rst

    def add_new(self, name, value=NONE, schema=None):
        if value is not NONE and schema is None:
            schema = detect_input_schema_by_value(value)
        if name in self.keys():
            raise InputAlreadyExists()
        self._instance.meta_inputs[name] = {'schema': schema}
        self[name] = value if value is not NONE else None
        return True

    def remove_existing(self, name):
        del self[name]
        del self._instance.meta_inputs[name]
        return True


class InputsField(IndexField):
    _wrp_class = InputsFieldWrp

    def __set__(self, instance, value):
        wrp = getattr(instance, self.fname)
        instance._data_container[self.fname] = self.default
        for inp_name, inp_value in value.iteritems():
            wrp[inp_name] = inp_value


class TagsFieldWrp(IndexFieldWrp):
    def __getitem__(self, name):
        raise TypeError('You cannot get tags like this')

    def __setitem__(self, name, value):
        raise TypeError('You cannot set tags like this')

    def __delitem__(self, name, value):
        raise TypeError('You cannot set tags like this')

    def __iter__(self):
        return iter(self._instance._data_container[self.fname])

    def as_list(self):
        try:
            return self._instance._data_container[self.fname][:]
        except KeyError:
            return []

    def set(self, name, value=None):
        if '=' in name and value is None:
            name, value = name.split('=', 1)
        if value is None:
            value = ''
        full_value = '{}={}'.format(name, value)
        inst = self._instance
        try:
            fld = inst._data_container[self.fname]
        except IndexError:
            fld = inst._data_container[self.fname] = []
        if full_value in fld:
            return
        # indexes = inst._riak_object.indexes.copy()  # copy it
        inst._add_index('{}_bin'.format(self.fname), '{}~{}'.format(name,
                                                                    value))
        try:
            fld.append(full_value)
        except KeyError:
            fld = [full_value]
        return True

    def has_tag(self, name, subval=None):
        fld = self._instance._data_container[self.fname]
        if name not in fld:
            return False
        if subval is not None:
            subvals = fld[name]
            return subval in subvals
        return True

    def remove(self, name, value=None):
        if '=' in name and value is None:
            name, value = name.split('=', 1)
        if value is None:
            value = ''
        inst = self._instance
        fld = inst._data_container[self.fname]
        full_value = '{}={}'.format(name, value)
        try:
            fld.remove(full_value)
        except ValueError:
            pass
        else:
            inst._remove_index('{}_bin'.format(self.fname), '{}~{}'.format(
                name, value))
        return True


class TagsField(IndexField):
    _wrp_class = TagsFieldWrp

    def __set__(self, instance, value):
        wrp = getattr(instance, self.fname)
        instance._data_container[self.fname] = self.default
        for val in value:
            wrp.set(val)

    def filter(self, name, subval=None):
        check_state_for('index', self._declared_in)
        if '=' in name and subval is None:
            name, subval = name.split('=', 1)
        if subval is None:
            subval = ''
        if not isinstance(subval, basestring):
            subval = str(subval)
        # maxresults because of riak bug with small number of results
        # https://github.com/basho/riak/issues/608
        declared = self._declared_in
        if not subval.endswith('*'):
            res = declared._get_index('{}_bin'.format(self.fname),
                                      startkey='{}~{}'.format(name, subval),
                                      endkey='{}~{} '.format(name, subval),
                                      max_results=100000,
                                      return_terms=True).results
        else:
            subval = subval.replace('*', '')
            res = declared._get_index('{}_bin'.format(self.fname),
                                      startkey='{}~{}'.format(name, subval),
                                      endkey='{}~{}~'.format(name, subval),
                                      max_results=100000,
                                      return_terms=True).results
        return set(map(itemgetter(1), res))

# class MetaInput(NestedModel):

#     name = Field(str)
#     schema = Field(str)
#     value = None  # TODO: implement it
#     is_list = Field(bool)
#     is_hash = Field(bool)


class Resource(Model):

    name = Field(str)

    version = Field(str)
    base_name = Field(str)
    base_path = Field(str)
    actions_path = Field(str)
    actions = Field(dict)
    handler = Field(str)
    meta_inputs = Field(dict, default=dict)
    state = Field(str)  # on_set/on_get would be useful
    events = Field(list, default=list)
    managers = Field(list, default=list)

    inputs = InputsField(default=dict)
    tags = TagsField(default=list)

    updated = IndexedField(StrInt)

    def _connect_single(self, other_inputs, other_name, my_name):
        if isinstance(other_name, (list, tuple)):
            # XXX: could be paralelized
            for other in other_name:
                other_inputs.connect(other, self, my_name)
        else:
            other_inputs.connect(other_name, self, my_name)

    def connect(self, other, mapping):
        other_inputs = other.inputs
        if mapping is None:
            return
        if self == other:
            for k, v in mapping.items():
                if k == v:
                    raise Exception('Trying to connect value-.* to itself')
        solar_map(
            lambda (my_name, other_name): self._connect_single(other_inputs,
                                                               other_name,
                                                               my_name),
            mapping.iteritems(),
            concurrency=2)

    def disconnect(self, other, inputs):
        def _to_disconnect((emitter, receiver, meta)):
            if not receiver[0] == other_key:
                return False
            # name there?
            if not emitter[0] == self.key:
                return False
            key = emitter[1]
            if key not in converted:
                return False
            convs = converted[key]
            for conv in convs:
                if conv:
                    if meta['tag'] == conv['tag'] \
                       and meta['destination_key'] == conv['destination_key']:
                        return True
                else:
                    return True
            return False

        def _convert_input(input):
            spl = input.split('|')
            spl_len = len(spl)
            if spl_len == 1:
                # normal input
                return input, None
            elif spl_len == 3:
                return spl[0], {'tag': spl[1], 'destination_key': spl[2]}
            else:
                raise Exception("Cannot convert input %r" % input)

        def _format_for_disconnect((emitter, receiver, meta)):
            input = receiver[1]
            if not meta:
                return "{}|{}|{}".format(receiver[1], emitter[0], emitter[1])
            dest_key = meta['destination_key']
            tag = meta.get('tag', other.name)
            return '{}:{}|{}'.format(input, dest_key, tag)

        converted = defaultdict(list)
        for k, v in map(_convert_input, inputs):
            converted[k].append(v)
        other_key = other.key
        edges = other.inputs._edges()
        edges = filter(_to_disconnect, edges)
        inputs = map(_format_for_disconnect, edges)
        solar_map(other.inputs.disconnect, inputs, concurrency=2)

    def save(self, *args, **kwargs):
        if self.changed():
            self.updated = StrInt()
        return super(Resource, self).save(*args, **kwargs)

    @classmethod
    def childs(cls, parents):

        all_indexes = cls.bucket.get_index('inputs_recv_bin',
                                           startkey='',
                                           endkey='~',
                                           return_terms=True,
                                           max_results=999999)

        tmp = defaultdict(set)
        to_visit = parents[:]
        visited = set()

        for item in all_indexes.results:
            data = item[0].split('|')
            em, rcv = data[0], data[2]
            tmp[rcv].add(em)

        while to_visit:
            n = to_visit.pop()
            for child in tmp[n]:
                if child not in visited:
                    to_visit.append(child)
            visited.add(n)
        return visited

    def delete(self):
        inputs_index = self.bucket.get_index('inputs_emit_bin',
                                             startkey=self.key,
                                             endkey=self.key + '~',
                                             return_terms=True,
                                             max_results=999999)

        to_disconnect_all = defaultdict(list)
        for emit_bin in inputs_index.results:
            index_vals = emit_bin[0].split('|')
            index_vals_len = len(index_vals)
            if index_vals_len == 6:  # hash
                (_, my_input, other_res,
                 other_input, my_tag, my_val) = index_vals
                to_disconnect_all[other_res].append("{}|{}|{}".format(
                    my_input, my_tag, my_val))
            elif index_vals_len == 4:
                _, my_input, other_res, other_input = index_vals
                to_disconnect_all[other_res].append(other_input)
            else:
                raise Exception("Unknown input %r" % index_vals)
        for other_obj_key, to_disconnect in to_disconnect_all.items():
            other_obj = Resource.get(other_obj_key)
            self.disconnect(other_obj, to_disconnect)
        super(Resource, self).delete()


class CommitedResource(Model):

    inputs = Field(dict, default=dict)
    connections = Field(list, default=list)
    base_path = Field(str)
    tags = Field(list, default=list)
    state = Field(str, default=lambda: 'removed')


"""
Type of operations:

- load all tasks for execution
- load single task + childs + all parents
  of childs (and transitions between them)
"""


class TasksFieldWrp(IndexFieldWrp):
    def add(self, task):
        return True

    def __iter__(self):
        return iter(self._instance._data_container[self.fname])

    def all(self, postprocessor=None):
        if postprocessor:
            return map(postprocessor, self)
        return list(self)

    def all_names(self):
        return self.all(lambda key: key.split('~')[1])

    def all_tasks(self):
        return self.all(Task.get)

    def _add(self, parent, child):
        parent._data_container['childs'].append(child.key)
        child._data_container['parents'].append(parent.key)

        child._add_index('childs_bin', parent.key)
        parent._add_index('parents_bin', child.key)
        return True


class TasksField(IndexField):

    _wrp_class = TasksFieldWrp

    def __set__(self, obj, value):
        wrp = getattr(obj, self.fname)
        obj._data_container[self.fname] = self.default
        for val in value:
            wrp.add(val)

    def _parse_key(self, startkey):
        return startkey


class ChildFieldWrp(TasksFieldWrp):
    def add(self, task):
        return self._add(self._instance, task)


class ChildField(TasksField):

    _wrp_class = ChildFieldWrp


class ParentFieldWrp(TasksFieldWrp):
    def add(self, task):
        return self._add(task, self._instance)


class ParentField(TasksField):

    _wrp_class = ParentFieldWrp


class Task(Model):
    """Node object"""

    name = Field(basestring)
    status = Field(basestring)
    target = Field(basestring, default=str)
    task_type = Field(basestring)
    args = Field(list)
    errmsg = Field(basestring, default=str)

    execution = IndexedField(basestring)
    parents = ParentField(default=list)
    childs = ChildField(default=list)

    @classmethod
    def new(cls, data):
        key = '%s~%s' % (data['execution'], data['name'])
        return Task.from_dict(key, data)


"""
system log

1. one bucket for all log items
2. separate logs for stage/history (using index)
3. last log item for resource in history
4. log item in staged log for resource|action
5. keep order of history
"""

_connection, _connection_details = parse_database_conn(C.solar_db)
if _connection.mode == 'sqlite':
    class NegativeCounter(Model):

        count = Field(int, default=int)

        def next(self):
            self.count -= 1
            self.save()
            return self.count
else:
    class NegativeCounter(Model):

        bucket_type = C.counter_bucket_type

        def next(self):
            ro = self._riak_object
            ro.decrement(1)
            ro.store()
            val = ro.value
            return val

        @property
        def count(self):
            return self._riak_object.value

        @classmethod
        def get_or_create(cls, key):
            return cls.get(key)

        @classmethod
        def get(cls, key):
            try:
                return cls._c.obj_cache.get(key)
            except KeyError:
                riak_object = cls.bucket.get(key)
                return cls.from_riakobj(riak_object)


class LogItem(Model):

    uid = IndexedField(basestring, default=lambda: str(uuid4()))
    resource = Field(basestring)
    action = Field(basestring)
    diff = Field(list)
    connections_diff = Field(list)
    state = Field(basestring)
    base_path = Field(basestring)  # remove me
    updated = Field(StrInt)

    history = IndexedField(StrInt)
    log = Field(basestring)  # staged/history

    composite = CompositeIndexField(fields=('log', 'resource', 'action'))

    @property
    def log_action(self):
        return '.'.join((self.resource, self.action))

    @classmethod
    def history_last(cls):
        items = cls.history.filter(StrInt.n_max(),
                                   StrInt.n_min(),
                                   max_results=1)
        if not items:
            return None
        return cls.get(items[0])

    def save(self):
        if any(f in self._modified_fields for f in LogItem.composite.fields):
            self.composite.reset()

        if 'log' in self._modified_fields and self.log == 'history':
            self.history = StrInt(next(NegativeCounter.get_or_create(
                'history')))
        return super(LogItem, self).save()

    @classmethod
    def new(cls, data):
        vals = {}
        if 'uid' not in vals:
            vals['uid'] = cls.uid.default
        vals.update(data)
        return LogItem.from_dict(vals['uid'], vals)


class Lock(Model):

    bucket_properties = {
        'backend': 'lock_bitcask_mult',
    }
    bucket_type = C.lock_bucket_type

    identity = Field(basestring)
    lockers = Field(list, default=list)

    @classmethod
    def _reduce(cls, lockers):
        # TODO: (jnowak) we could remove not needed lockers there
        # not needed means already replaced by other lock.
        _s = set()
        for x in lockers:
            _s.add(tuple(x))
        res = [list(x) for x in _s]
        return res

    def sum_all(self):
        reduced = self.reduce()
        _pos = defaultdict(int)
        _neg = defaultdict(int)
        for locker, val, stamp in reduced:
            k = (locker, stamp)
            if val < 0:
                if k in _pos:
                    del _pos[k]
                else:
                    _neg[k] = -1
            elif val > 0:
                if k in _neg:
                    del _neg[k]
                else:
                    _pos[k] = 1
        # TODO: (jnowak) consider discard all orphaned releases
        # # key_diff = set(_neg.keys()) - set(_pos.keys())
        # # for k in key_diff:
        # #     del _neg[k]
        return {locker: val for ((locker, stamp), val) in chain(
            _pos.items(),
            _neg.items()
        )}

    def reduce(self):
        lockers = self.lockers
        self.lockers = self._reduce(lockers)
        return self.lockers

    def am_i_locking(self, uid):
        return self.who_is_locking() == uid

    def who_is_locking(self):
        try:
            if self.identity:
                return self.identity
            return None
        except KeyError:
            summed = self.sum_all()
            if not summed:
                return None
            to_max = sorted([(v, k) for (k, v) in summed.items()])[-1]
            if to_max[0] > 0:
                return to_max[1]
            return None

    def change_locking_state(self, uid, value, stamp):
        try:
            if self.identity:
                if value:
                    self.identity = uid
                else:
                    raise Exception("Unsupported operation, to release "
                                    "this lock you need to delete it.")
                return True
        except KeyError:
            self.lockers.append([uid, value, stamp])
            self.reduce()
            return True

    def save(self, *args, **kwargs):
        self.reduce()
        super(Lock, self).save(*args, **kwargs)

    @staticmethod
    def conflict_resolver(riak_object):
        siblings = riak_object.siblings
        sdatas = map(lambda x: x.data.get('lockers', []), siblings)
        l = []
        for data in sdatas:
            l.extend(data)
        reduced = Lock._reduce(l)
        first_sibling = siblings[0]
        first_sibling.data['lockers'] = reduced
        riak_object.siblings = [first_sibling]
        # del Lock._c.obj_cache[riak_object.key]
