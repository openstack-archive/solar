from solar.interfaces.db import get_db
from solar.events.api import add_events
from solar.events.controls import Dependency


db = get_db()


def guess_mapping(emitter, receiver):
    """Guess connection mapping between emitter and receiver.

    Suppose emitter and receiver have common inputs:
    ip, ssh_key, ssh_user

    Then we return a connection mapping like this:

    {
        'ip': '<receiver>.ip',
        'ssh_key': '<receiver>.ssh_key',
        'ssh_user': '<receiver>.ssh_user'
    }

    :param emitter:
    :param receiver:
    :return:
    """
    guessed = {}
    for key in emitter.args:
        if key in receiver.args:
            guessed[key] = key

    return guessed


def connect(emitter, receiver, mapping={}, events=None):
    mapping = mapping or guess_mapping(emitter, receiver)

    if isinstance(mapping, set):
        for src in mapping:
            connect_single(emitter, src, receiver, src)
        return

    for src, dst in mapping.items():
        if isinstance(dst, list):
            for d in dst:
                connect_single(emitter, src, receiver, d)
            continue

        connect_single(emitter, src, receiver, dst)


def connect_single(emitter, src, receiver, dst):
    # Disconnect all receiver inputs
    # Check if receiver input is of list type first
    emitter_input = emitter.resource_inputs()[src]
    receiver_input = receiver.resource_inputs()[dst]

    if not receiver_input.properties['is_list']:
        db.delete_relations(
            dest=receiver_input,
            type_=db.RELATION_TYPES.input_to_input
        )

    # Check for cycles
    r = db.get_relations(
        receiver_input,
        emitter_input,
        type_=db.RELATION_TYPES.input_to_input
    )

    if r:
        raise Exception('Prevented creating a cycle')

    db.get_or_create_relation(
        emitter_input,
        receiver_input,
        properties={},
        type_=db.RELATION_TYPES.input_to_input
    )


def disconnect_receiver_by_input(receiver, input_name):
    input_node = receiver.resource_inputs()[input_name]

    db.delete_relations(
        dest=input_node,
        type_=db.RELATION_TYPES.input_to_input
    )


def disconnect(emitter, receiver):
    for emitter_input in emitter.resource_inputs().values():
        for receiver_input in receiver.resource_inputs().values():
            db.delete_relations(
                source=emitter_input,
                dest=receiver_input,
                type_=db.RELATION_TYPES.input_to_input
            )
