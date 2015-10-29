from solar.dblayer.model import (Model, Field, IndexField,
                                 IndexFieldWrp,
                                 DBLayerException,
                                 requires_clean_state, check_state_for,
                                 StrInt,
                                 IndexedField)
from types import NoneType
from operator import itemgetter
from enum import Enum

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


    # def _connect_dict_simple(self, my_resource, my_inp_name, other_resource, other_inp_name):
    #     if ':' in other_inp_name:
    #         raise NotImplementedError("Not supported `:` in this direction")
    #     if ':' in my_inp_name:
    #         my_inp_name, nested_key = my_inp_name.split(':', 1)
    #     else:
    #         nested_key = ""

    #     if '|' in nested_key:
    #         nested_key, nested_tag = nested_key.split('|', 1)
    #     else:
    #         nested_tag = other_resource.key
    #     raise NotImplementedError()


    # def _connect_list_simple(self, my_resource, my_inp_name, other_resource, other_inp_name):
    #     other_ind_name = '{}_emit_bin'.format(self.fname)
    #     other_ind_val = '{}|{}|{}|{}'.format(other_resource.key,
    #                                          other_inp_name,
    #                                          my_resource.key,
    #                                          my_inp_name)

    #     my_ind_name = '{}_recv_bin'.format(self.fname)
    #     my_ind_val = '{}|{}|{}|{}'.format(my_resource.key,
    #                                       my_inp_name,
    #                                       other_resource.key,
    #                                       other_inp_name)

    #     my_resource._add_index(my_ind_name,
    #                            my_ind_val)
    #     my_resource._add_index(other_ind_name,
    #                            other_ind_val)
    #     try:
    #         del self._cache[my_inp_name]
    #     except KeyError:
    #         pass
    #     return True


    # def _connect_simple_simple(self, my_resource, my_inp_name, other_resource, other_inp_name):
    #     # TODO: for now connections are attached to target resource
    #     # in future we might change it to separate object

    #     other_ind_name = '{}_emit_bin'.format(self.fname)
    #     other_ind_val = '{}|{}|{}|{}'.format(other_resource.key,
    #                                          other_inp_name,
    #                                          my_resource.key,
    #                                          my_inp_name)

    #     my_ind_name = '{}_recv_bin'.format(self.fname)
    #     my_ind_val = '{}|{}|{}|{}'.format(my_resource.key,
    #                                       my_inp_name,
    #                                       other_resource.key,
    #                                       other_inp_name)

    #     # ensure no conflicting connections are done
    #     # TODO: move this to backend layer
    #     indexes = my_resource._riak_object.indexes
    #     to_del = []
    #     for ind_name, ind_value in indexes:
    #         if ind_name == my_ind_name:
    #             mr, mn = ind_value.split('|')[:2]
    #             if mr == my_resource.key and mn == my_inp_name:
    #                 to_del.append((ind_name, ind_value))
    #         elif ind_name == other_ind_name:
    #             mr, mn = ind_value.rsplit('|')[2:]
    #             if mr == my_resource.key and mn == my_inp_name:
    #                 to_del.append((ind_name, ind_value))

    #     for ind_name, ind_value in to_del:
    #         my_resource._remove_index(ind_name, value=ind_value)

    #     # add new
    #     my_resource._add_index(my_ind_name,
    #                            my_ind_val)
    #     my_resource._add_index(other_ind_name,
    #                            other_ind_val)
    #     try:
    #         del self._cache[my_inp_name]
    #     except KeyError:
    #         pass
    #     return True


    def _input_type(self, resource, name):
        # XXX: it could be worth to precalculate it
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


    def _connect_my_simple(self, my_resource, my_inp_name, other_resource, other_inp_name):
        my_ind_name = '{}_recv_bin'.format(self.fname)
        my_ind_val = '{}|{}|{}|{}'.format(my_resource.key,
                                          my_inp_name,
                                          other_resource.key,
                                          other_inp_name)


        my_resource._add_index(my_ind_name, my_ind_val)
        return True

    def _connect_other_simple(self, my_resource, my_inp_name, other_resource, other_inp_name):
        other_ind_name = '{}_emit_bin'.format(self.fname)
        other_ind_val = '{}|{}|{}|{}'.format(other_resource.key,
                                             other_inp_name,
                                             my_resource.key,
                                             my_inp_name)
        my_resource._add_index(other_ind_name,
                               other_ind_val)
        return True


    def connect(self, my_inp_name, other_resource, other_inp_name):
        my_resource = self._instance
        other_type = self._input_type(other_resource, other_inp_name)
        my_type = self._input_type(my_resource, my_inp_name)

        if my_type == other_type:
            my_type = InputTypes.simple
            other_type = InputTypes.simple

        # set my side
        my_meth = getattr(self, '_connect_my_{}'.format(my_type.name))
        my_meth(my_resource, my_inp_name, other_resource, other_inp_name)

        # set other side
        other_meth = getattr(self, '_connect_other_{}'.format(other_type.name))
        other_meth(my_resource, my_inp_name, other_resource, other_inp_name)

        try:
            del self._cache[my_inp_name]
        except KeyError:
            pass
        return True
        # raise Exception()
        # if ':' in my_inp_name:
        #     tmp_name = my_inp_name.split(':', 1)[0]
        #     my_input = self._get_raw_field_val(tmp_name)
        # else:
        #     my_input = self._get_raw_field_val(my_inp_name)
        # other_input = other_resource.inputs._get_raw_field_val(other_inp_name)
        # if isinstance(my_input, self._simple_types):
        #     my_side = 'simple'
        # else:
        #     my_side = type(my_input).__name__
        # if isinstance(other_input, self._simple_types):
        #     other_side = 'simple'
        # else:
        #     other_side = type(other_input).__name__
        # method = '_connect_{}_{}'.format(my_side, other_side)
        # try:
        #     meth = getattr(self, method)
        # except AttributeError:
        #     raise Exception("Unknown connection %r %r" % (my_side, other_side))
        # else:
        #     return meth(my_resource, my_inp_name, other_resource, other_inp_name)

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

    def _get_field_val(self, name):
        # maybe it should be tco
        check_state_for('index', self._instance)
        try:
            return self._cache[name]
        except KeyError:
            pass
        fname = self.fname
        my_name = self._instance.key
        self._has_own_input(name)
        ind_name = '{}_recv_bin'.format(fname)
        # XXX: possible optimization
        # get all values for resource and cache it (use dirty to check)
        recvs = self._instance._get_index(ind_name,
                                          startkey='{}|{}|'.format(my_name, name),
                                          endkey='{}|{}|~'.format(my_name, name),
                                          return_terms=True).results
        if not recvs:
            _res = self._get_raw_field_val(name)
            self._cache[name] = _res
            return _res
        recvs = recvs[0]
        index_val, obj_key = recvs
        _, inp, emitter_key, emitter_inp = index_val.split('|', 4)
        res = Resource.get(emitter_key).inputs._get_field_val(emitter_inp)
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
            inp, emitter_name, emitter_inp = recvs[0].split('|', 3)
            raise Exception("I'm connected with resource %r input %r" % (emitter_name, emitter_inp))
        # inst = self._instance
        robj = self._instance._riak_object
        self._instance._add_index('%s_bin' % self.fname, '{}|{}'.format(my_name, name))
        try:
            robj.data[self.fname][name] = value
        except KeyError:
            robj.data[self.fname] = {name: value}
        self._cache[name] = value
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

    def set(self, name, value=None):
        if '=' in name and value is None:
            name, value = name.split('=', 1)
        if value is None:
            value = ''
        inst = self._instance
        indexes = inst._riak_object.indexes.copy()  # copy it

        inst._add_index('{}_bin'.format(self.fname), '{}~{}'.format(name, value))
        try:
            fld = inst._data_container[self.fname]
        except IndexError:
            fld = inst._data_container[self.fname] = []
        full_value = '{}={}'.format(name, value)
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

    inputs = InputsField(default=dict)
    tags = TagsField(default=list)

    updated = IndexedField(StrInt)

    def connect(self, other, mappings):
        my_inputs = self.inputs
        other_inputs = other.inputs
        for my_name, other_name in mappings.iteritems():
            other_inputs.connect(other_name, self, my_name)

    def save(self, *args, **kwargs):
        if self.changed():
            self.updated = StrInt()
        return super(Resource, self).save(*args, **kwargs)
