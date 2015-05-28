
class Profile(object):

    def __init__(self, profile):
        self._profile = profile
        self.tags = set(profile['tags'])
        self.extensions = profile.get('extensions', [])
        self.connections = profile.get('connections', [])

    def get(self, key):
        return self._profile.get(key, None)
