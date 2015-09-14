import abc
from enum import Enum
from functools import partial


class Node(object):
    def __init__(self, db, uid, labels, properties):
        self.db = db
        self.uid = uid
        self.labels = labels
        self.properties = properties

    @property
    def collection(self):
        return getattr(
            BaseGraphDB.COLLECTIONS,
            list(self.labels)[0]
        )


class Relation(object):
    def __init__(self, db, start_node, end_node, properties):
        self.db = db
        self.start_node = start_node
        self.end_node = end_node
        self.properties = properties


class DBObjectMeta(abc.ABCMeta):
    # Tuples of: function name, is-multi (i.e. returns a list)
    node_db_read_methods = [
        ('all', True),
        ('create', False),
        ('get', False),
        ('get_or_create', False),
    ]
    relation_db_read_methods = [
        ('all_relations', True),
        ('create_relation', False),
        ('get_relations', True),
        ('get_relation', False),
        ('get_or_create_relation', False),
    ]

    def __new__(cls, name, parents, dct):
        def from_db_list_decorator(converting_func, method):
            def wrapper(self, *args, **kwargs):
                db_convert = kwargs.pop('db_convert', True)

                result = method(self, *args, **kwargs)

                if db_convert:
                    return map(partial(converting_func, self), result)

                return result

            return wrapper

        def from_db_decorator(converting_func, method):
            def wrapper(self, *args, **kwargs):
                db_convert = kwargs.pop('db_convert', True)

                result = method(self, *args, **kwargs)

                if result is None:
                    return

                if db_convert:
                    return converting_func(self, result)

                return result

            return wrapper

        node_db_to_object = cls.find_method(
            'node_db_to_object', name, parents, dct
        )
        relation_db_to_object = cls.find_method(
            'relation_db_to_object', name, parents, dct
        )

        # Node conversions
        for method_name, is_list in cls.node_db_read_methods:
            method = cls.find_method(method_name, name, parents, dct)
            if is_list:
                func = from_db_list_decorator
            else:
                func = from_db_decorator
            dct[method_name] = func(node_db_to_object, method)

        # Relation conversions
        for method_name, is_list in cls.relation_db_read_methods:
            method = cls.find_method(method_name, name, parents, dct)
            if is_list:
                func = from_db_list_decorator
            else:
                func = from_db_decorator
            dct[method_name] = func(relation_db_to_object, method)

        return super(DBObjectMeta, cls).__new__(cls, name, parents, dct)

    @classmethod
    def find_method(cls, method_name, class_name, parents, dict):
        if method_name in dict:
            return dict[method_name]

        for parent in parents:
            method = getattr(parent, method_name)
            if method:
                return method

        raise NotImplementedError(
            '"{}" method not implemented in class {}'.format(
                method_name, class_name
            )
        )


class BaseGraphDB(object):
    __metaclass__ = DBObjectMeta

    COLLECTIONS = Enum(
        'Collections',
        'input resource state_data state_log plan_node plan_graph events stage_log commit_log'
    )
    DEFAULT_COLLECTION=COLLECTIONS.resource
    RELATION_TYPES = Enum(
        'RelationTypes',
        'input_to_input resource_input plan_edge graph_to_node'
    )
    DEFAULT_RELATION=RELATION_TYPES.resource_input

    @staticmethod
    def node_db_to_object(node_db):
        """Convert node DB object to Node object."""

    @staticmethod
    def object_to_node_db(node_obj):
        """Convert Node object to node DB object."""

    @staticmethod
    def relation_db_to_object(relation_db):
        """Convert relation DB object to Relation object."""

    @staticmethod
    def object_to_relation_db(relation_obj):
        """Convert Relation object to relation DB object."""

    @abc.abstractmethod
    def all(self, collection=DEFAULT_COLLECTION):
        """Return all elements (nodes) of type `collection`."""

    @abc.abstractmethod
    def all_relations(self, type_=DEFAULT_RELATION):
        """Return all relations of type `type_`."""

    @abc.abstractmethod
    def clear(self):
        """Clear the whole DB."""

    @abc.abstractmethod
    def clear_collection(self, collection=DEFAULT_COLLECTION):
        """Clear all elements (nodes) of type `collection`."""

    @abc.abstractmethod
    def create(self, name, properties={}, collection=DEFAULT_COLLECTION):
        """Create element (node) with given name, args, of type `collection`."""

    @abc.abstractmethod
    def create_relation(self,
                        source,
                        dest,
                        properties={},
                        type_=DEFAULT_RELATION):
        """
        Create relation (connection) of type `type_` from source to dest with
        given args.
        """

    @abc.abstractmethod
    def get(self, name, collection=DEFAULT_COLLECTION):
        """Fetch element with given name and collection type."""

    @abc.abstractmethod
    def get_or_create(self,
                      name,
                      properties={},
                      collection=DEFAULT_COLLECTION):
        """
        Fetch or create element (if not exists) with given name, args of type
        `collection`.
        """

    @abc.abstractmethod
    def delete_relations(self,
                         source=None,
                         dest=None,
                         type_=DEFAULT_RELATION):
        """Delete all relations of type `type_` from source to dest."""

    @abc.abstractmethod
    def get_relations(self,
                      source=None,
                      dest=None,
                      type_=DEFAULT_RELATION):
        """Fetch all relations of type `type_` from source to dest.

        NOTE that this function must return only direct relations (edges)
        between vertices `source` and `dest` of type `type_`.

        If you want all PATHS between `source` and `dest`, write another
        method for this (`get_paths`)."""

    @abc.abstractmethod
    def get_relation(self, source, dest, type_=DEFAULT_RELATION):
        """Fetch relations with given source, dest and type_."""

    @abc.abstractmethod
    def get_or_create_relation(self,
                               source,
                               dest,
                               properties={},
                               type_=DEFAULT_RELATION):
        """Fetch or create relation with given args."""
