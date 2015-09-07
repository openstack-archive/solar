import abc
from enum import Enum


class BaseGraphDB(object):
    __metaclass__ = abc.ABCMeta

    COLLECTIONS = Enum(
        'Collections',
        'input resource state_data state_log'
    )
    DEFAULT_COLLECTION=COLLECTIONS.resource
    RELATION_TYPES = Enum(
        'RelationTypes',
        'input_to_input resource_input'
    )
    DEFAULT_RELATION=RELATION_TYPES.resource_input

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
    def create(self, name, args={}, collection=DEFAULT_COLLECTION):
        """Create element (node) with given name, args, of type `collection`."""

    @abc.abstractmethod
    def create_relation(self,
                        source,
                        dest,
                        args={},
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
                      args={},
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
        """Fetch all relations of type `type_` from source to dest."""

    @abc.abstractmethod
    def get_relation(self, source, dest, type_=DEFAULT_RELATION):
        """Fetch relations with given source, dest and type_."""

    @abc.abstractmethod
    def get_or_create_relation(self,
                               source,
                               dest,
                               args={},
                               type_=DEFAULT_RELATION):
        """Fetch or create relation with given args."""
