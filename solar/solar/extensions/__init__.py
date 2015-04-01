
from solar.extensions import playbook


def resource(config):
    return playbook.Playbook(config)
