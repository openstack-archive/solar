from solar import extensions
from solar import errors


class ExtensionsManager(object):

    def __init__(self, profile):
        self.profile = profile
    def get_data(self, key):
        """Finds data by extensions provider"""
        providers = filter(lambda e: key in e.PROVIDES, extensions.get_all_extensions())

        if not providers:
            raise errors.CannotFindExtension('Cannot find extension which provides "{0}"'.format(key))

        return getattr(providers[0](self.profile), key)()
