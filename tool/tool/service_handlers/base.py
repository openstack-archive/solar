

class BaseService(object):

    def __init__(self, resources, hosts='all'):
        self.hosts = hosts
        self.resources = resources

    def run(self):
        for resource in self.resources:
            yield resource.run()

# how service should be different from resources, apart from providing
# additional data?
