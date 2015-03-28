

from tool.profile_handlers import ansible


def process(profile, resources):

    # it should be a fabric
    return ansible.process(profile, resources)
