from solar import extensions
from solar import errors


class ExtensionsManager(object):

    def __init__(self):
        # TODO: probably we should pass as a parameter profile, global
        # config with specific versions of extensions
        pass

    def get_data(self, key):
        """Finds data by extensions provider"""
        providers = filter(lambda e: key in e.PROVIDES, extensions.get_all_extensions())

        if not providers:
            raise errors.CannotFindExtension('Cannot find extension which provides "{0}"'.format(key))

        return getattr(providers[0](), key)()
