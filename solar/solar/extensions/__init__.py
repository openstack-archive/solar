import glob
import os

from solar import utils
from solar.core.profile import Profile
from solar.extensions.base import BaseExtension
# Import all modules from the directory in order
# to make subclasses for extensions work
modules = glob.glob(os.path.join(os.path.dirname(__file__), 'modules', '*.py'))
[__import__('%s.%s' % ('modules', os.path.basename(f)[:-3]), locals(), globals()) for f in modules]


def get_all_extensions():
    return BaseExtension.__subclasses__()


def find_extension(id_, version):
    extensions = filter(
        lambda e: e.ID == id_ and e.VERSION == version,
        get_all_extensions())

    if not extensions:
        return None

    return extensions[0]


def find_by_provider_from_profile(profile, provider):
    profile_ = Profile(profile)
    extensions = profile_.extensions
    result = None
    for ext in extensions:
        result = find_extension(ext['id'], ext['version'])
        if result:
            break

    return result(profile_)
