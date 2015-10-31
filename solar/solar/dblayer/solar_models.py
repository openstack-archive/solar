from solar.dblayer.model import (Model, Field, IndexField,
                                 IndexFieldWrp,
                                 DBLayerException,
                                 requires_clean_state, check_state_for,
                                 StrInt,
                                 IndexedField, CompositeIndexField)
from types import NoneType
from operator import itemgetter
from enum import Enum
from itertools import groupby
from uuid import uuid4

InputTypes = Enum('InputTypes',
                  'simple list hash list_hash')


class DBLayerSolarException(DBLayerException):
    pass


class InputsFieldWrp(IndexFieldWrp):

    _simple_types = (NoneType, int, float, basestring, str, unicode)

    def __init__(self, *args, **kwargs):
        super(InputsFieldWrp, self).__init__(*args, **kwargs)
        # TODO: add cache for lookup
        self._cache = {}

    def _input_type(self, resource, name):
        # XXX: it could be worth to precalculate it
        if ':' in name:
            name = name.split(":", 1)[0]
        schema = resource.meta_inputs[name]['schema']
        if isinstance(schema, self._simple_types):
            return InputTypes.simple
        if isinstance(schema, list):
            if len(schema) > 0 and isinstance(schema[0], dict):
                return InputTypes.list_hash
            return InputTypes.list
        if isinstance(schema, dict):
            return InputTypes.hash
        raise Exception("Unknown type")

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
                meta = {'destination_key': data[5],
                        'tag': data[4]}
            else:
                raise Exception("Unsupported case")
            yield (my_resource, my_input), (other_resource, other_input), meta

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

    def as_dict(self):
        # TODO: could be paralelized
        return dict((name, self._get_field_val(name)) for name in self)

    def _connect_my_simple(self, my_resource, my_inp_name, other_resource, other_inp_name, my_type, other_type):
        types_mapping = '|{}_{}'.format(my_type.value, other_type.value)
        my_ind_name = '{}_recv_bin'.format(self.fname)
        my_ind_val = '{}|{}|{}|{}'.format(my_resource.key,
                                          my_inp_name,
                                          other_resource.key,
                                          other_inp_name)
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

    def _connect_other_simple(self, my_resource, my_inp_name, other_resource, other_inp_name, my_type, other_type):
        other_ind_name = '{}_emit_bin'.format(self.fname)
        other_ind_val = '{}|{}|{}|{}'.format(other_resource.key,
                                             other_inp_name,
                                             my_resource.key,
                                             my_inp_name)

        real_my_type = self._input_type(my_resource, my_inp_name)
        if real_my_type == InputTypes.simple:
            for ind_name, ind_value in my_resource._riak_object.indexes:
                if ind_name == other_ind_name:
                    mr, mn = ind_value.rsplit('|')[2:]
                    if mr == my_resource.key and mn == my_inp_name:
                        my_resource._remove_index(ind_name, ind_value)
                        break

        my_resource._add_index(other_ind_name,
                               other_ind_val)
        return other_inp_name

    def _connect_other_hash(self, my_resource, my_inp_name, other_resource, other_inp_name, my_type, other_type):
        return self._connect_other_simple(my_resource, my_inp_name, other_resource, other_inp_name, my_type, other_type)

    def _connect_my_list(self, my_resource, my_inp_name, other_resource, other_inp_name, my_type, other_type):
        ret = self._connect_my_simple(my_resource, my_inp_name, other_resource, other_inp_name, my_type, other_type)
        return ret

    def _connect_my_hash(self, my_resource, my_inp_name, other_resource, other_inp_name, my_type, other_type):
        my_key, my_val = my_inp_name.split(':', 1)
        if '|' in my_val:
            my_val, my_tag = my_val.split('|', 1)
        else:
            my_tag = other_resource.name
        types_mapping = '|{}_{}'.format(my_type.value, other_type.value)
        my_ind_name = '{}_recv_bin'.format(self.fname)
        my_ind_val = '{}|{}|{}|{}|{}|{}'.format(my_resource.key,
                                                my_key,
                                                other_resource.key,
                                                other_inp_name,
                                                my_tag,
                                                my_val
        )
        my_ind_val += types_mapping

        my_resource._add_index(my_ind_name, my_ind_val)
        return my_key

    def _connect_my_list_hash(self, my_resource, my_inp_name, other_resource, other_inp_name, my_type, other_type):
        return self._connect_my_hash(my_resource, my_inp_name, other_resource, other_inp_name, my_type, other_type)

    def connect(self, my_inp_name, other_resource, other_inp_name):
        my_resource = self._instance
        other_type = self._input_type(other_resource, other_inp_name)
        my_type = self._input_type(my_resource, my_inp_name)

        if my_type == other_type:
            # if the type is the same map 1:1
            my_type = InputTypes.simple
            other_type = InputTypes.simple

        # set my side
        my_meth = getattr(self, '_connect_my_{}'.format(my_type.name))
        my_affected = my_meth(my_resource, my_inp_name, other_resource, other_inp_name, my_type, other_type)

        # set other side
        other_meth = getattr(self, '_connect_other_{}'.format(other_type.name))
        other_meth(my_resource, my_inp_name, other_resource, other_inp_name, my_type, other_type)

        try:
            del self._cache[my_affected]
        except KeyError:
            pass
        return True

    def _has_own_input(self, name):
        try:
            return self._cache[name]
        except KeyError:
            pass
        my_name = self._instance.key
        try:
            self._get_raw_field_val(name)
        except KeyError:
            raise DBLayerSolarException('No input {} for {}'.format(name, my_name))
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
        check_state_for('index', self._instance)
        fname = self.fname
        my_name = self._instance.key
        self._has_own_input(name)
        ind_name = '{}_recv_bin'.format(fname)
        # XXX: possible optimization
        # get all values for resource and cache it (use dirty to check)
        kwargs = dict(startkey='{}|{}|'.format(my_name, name),
                      endkey='{}|{}|~'.format(my_name, name),
                      return_terms=True)
        my_type = self._input_type(self._instance, name)
        if my_type == InputTypes.simple:
            kwargs['max_results'] = 1
        else:
            kwargs['max_results'] = 99999
        recvs = self._instance._get_index(ind_name,
                                          **kwargs).results
        if not recvs:
            _res = self._get_raw_field_val(name)
            self._cache[name] = _res
            if other:
                other_res = self._get_field_val(other)
                self._cache[full_name] = other_res
                return other_res
            return _res
        my_meth = getattr(self, '_map_field_val_{}'.format(my_type.name))
        return my_meth(recvs, my_name, other=other)


    def _map_field_val_simple(self, recvs, name, other=None):
        recvs = recvs[0]
        index_val, obj_key = recvs
        _, inp, emitter_key, emitter_inp, _mapping_type = index_val.split('|', 4)
        res = Resource.get(emitter_key).inputs._get_field_val(emitter_inp, other)
        self._cache[name] = res
        return res

    def _map_field_val_list(self, recvs, name, other=None):
        if len(recvs) == 1:
            recv = recvs[0]
            index_val, obj_key = recv
            _, inp, emitter_key, emitter_inp, mapping_type = index_val.split('|', 4)
            res = Resource.get(emitter_key).inputs._get_field_val(emitter_inp, other)
            if mapping_type != "{}_{}".format(InputTypes.simple.value, InputTypes.simple.value):
                res = [res]
        else:
            res = []
            for recv in recvs:
                index_val, obj_key = recv
                _, _, emitter_key, emitter_inp, mapping_type = index_val.split('|', 4)
                cres = Resource.get(emitter_key).inputs._get_field_val(emitter_inp, other)
                res.append(cres)
        self._cache[name] = res
        return res

    def _map_field_val_hash(self, recvs, name, other=None):
        if len(recvs) == 1:
            recv = recvs[0]
            index_val, obj_key = recv
            _, inp, emitter_key, emitter_inp, mapping_type = index_val.split('|', 4)
            res = Resource.get(emitter_key).inputs._get_field_val(emitter_inp, other)
            if mapping_type != "{}_{}".format(InputTypes.simple.value, InputTypes.simple.value):
                raise NotImplementedError()
        else:
            items = []
            tags = set()
            for recv in recvs:
                index_val, obj_key = recv
                _, _, emitter_key, emitter_inp, my_tag, my_val, mapping_type = index_val.split('|', 6)
                cres = Resource.get(emitter_key).inputs._get_field_val(emitter_inp, other)
                items.append((my_tag, my_val, cres))
                tags.add(my_tag)
            if len(tags) != 1:
                # TODO: add it also for during connecting
                raise Exception("Detected dict with different tags")
            res = {}
            for _, my_val, value in items:
                res[my_val] = value
        self._cache[name] = res
        return res

    def _map_field_val_list_hash(self, recvs, name, other=None):
        items = []
        tags = set()
        for recv in recvs:
            index_val, obj_key = recv
            _, _, emitter_key, emitter_inp, my_tag, my_val, mapping_type = index_val.split('|', 6)
            cres = Resource.get(emitter_key).inputs._get_field_val(emitter_inp, other)
            items.append((my_tag, my_val, cres))
        tmp_res = {}
        for my_tag, my_val, value in items:
            try:
                tmp_res[my_tag][my_val] = value
            except KeyError:
                tmp_res[my_tag] = {my_val: value}
        res = tmp_res.values()
        self._cache[name] = res
        return res

    def _get_raw_field_val(self, name):
        return self._instance._data_container[self.fname][name]

    def __getitem__(self, name):
        return self._get_field_val(name)

    def __delitem__(self, name):
        self._has_own_input(name)
        self._instance._field_changed(self)
        try:
            del self._cache[name]
        except KeyError:
            pass
        inst = self._instance
        inst._riak_object.remove_index('%s_bin' % self.fname, '{}|{}'.format(self._instance.key, name))
        del inst._data_container[self.fname][name]

    def __setitem__(self, name, value):
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
        recvs = self._instance._get_index(ind_name,
                                 startkey='{}|{}|'.format(my_name, name),
                                 endkey='{}|{}|~'.format(my_name,name),
                                 max_results=1,
                                 return_terms=True).results
        if recvs:
            recvs = recvs[0]
            res, inp, emitter_name, emitter_inp = recvs[0].split('|')[:4]
            raise Exception("%s:%s is connected with resource %s:%s" % (res, inp, emitter_name, emitter_inp))
        # inst = self._instance
        robj = self._instance._riak_object
        self._instance._add_index('%s_bin' % self.fname, '{}|{}'.format(my_name, name))
        try:
            robj.data[self.fname][name] = value
        except KeyError:
            robj.data[self.fname] = {name: value}
        self._cache[name] = value
        return True

    def to_dict(self):
        rst = {}
        for key in self._instance._data_container[self.fname].keys():
            rst[key] = self[key]
        return rst


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
        inst._add_index('{}_bin'.format(self.fname), '{}~{}'.format(name, value))
        try:
            fld.append(full_value)
        except KeyError:
            fld = [full_value]
        return True

    def has_tag(self, name, subval=None):
        fld = self._instance._data_container[self.fname]
        if not name in fld:
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
            vals = fld.remove(full_value)
        except ValueError:
            pass
        else:
            inst._remove_index('{}_bin'.format(self.fname), '{}~{}'.format(name, value))
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
        if not subval.endswith('*'):
            res = self._declared_in._get_index('{}_bin'.format(self.fname),
                                               startkey='{}~{}'.format(name, subval),
                                               endkey='{}~{} '.format(name, subval),  # space required
                                               max_results=100000,
                                               return_terms=True).results
        else:
            subval = subval.replace('*', '')
            res = self._declared_in._get_index('{}_bin'.format(self.fname),
                                               startkey='{}~{}'.format(name, subval),
                                               endkey='{}~{}~'.format(name, subval),  # space required
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
    puppet_module = Field(str)  # remove
    meta_inputs = Field(dict, default=dict)
    state = Field(str)  # on_set/on_get would be useful
    events = Field(list, default=list)

    inputs = InputsField(default=dict)
    tags = TagsField(default=list)


    updated = IndexedField(StrInt)

    def connect(self, other, mapping):
        my_inputs = self.inputs
        other_inputs = other.inputs
        if mapping is None:
            return
        for my_name, other_name in mapping.iteritems():
            other_inputs.connect(other_name, self, my_name)

    def save(self, *args, **kwargs):
        if self.changed():
            self.updated = StrInt()
        return super(Resource, self).save(*args, **kwargs)


class CommitedResource(Model):

    inputs = Field(dict, default=dict)
    connections = Field(list, default=list)
    base_path = Field(str)
    tags = Field(list, default=list)
    state = Field(str, default=lambda: 'removed')


"""
Type of operations:

- load all tasks for execution
- load single task + childs + all parents of childs (and transitions between them)
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

class NegativeCounter(Model):

    count = Field(int, default=int)

    def next(self):
        self.count -= 1
        self.save()
        return self.count


class LogItem(Model):

    uid = IndexedField(basestring, default=lambda: str(uuid4()))
    resource = Field(basestring)
    action = Field(basestring)
    diff = Field(list)
    connections_diff = Field(list)
    state = Field(basestring)
    base_path = Field(basestring) # remove me

    history = IndexedField(StrInt)
    log = Field(basestring) # staged/history

    composite = CompositeIndexField(fields=('log', 'resource', 'action'))

    @property
    def log_action(self):
        return '.'.join((self.resource, self.action))

    def save(self):
        if any(f in self._modified_fields for f in LogItem.composite.fields):
            self.composite.reset()

        if 'log' in self._modified_fields and self.log == 'history':
            self.history = StrInt(next(NegativeCounter.get_or_create('history')))
        return super(LogItem, self).save()

    @classmethod
    def new(cls, data):
        vals = {}
        if 'uid' not in vals:
            vals['uid'] = cls.uid.default
        vals.update(data)
        return LogItem.from_dict(vals['uid'], vals)
