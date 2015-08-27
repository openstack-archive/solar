from solar.interfaces.db import get_db


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


def connect(emitter, receiver, mapping={}):
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
        rel = db.get_relations(
            source=emitter_input,
            dest=receiver_input,
            type_=db.RELATION_TYPES.input_to_input
        )
        for r in rel:
            r.delete()

    db.get_or_create_relation(
        emitter_input,
        receiver_input,
        args={},
        type_=db.RELATION_TYPES.input_to_input
    )


def disconnect_receiver_by_input(receiver, input_name):
    input_node = receiver.resource_inputs()[input_name]

    for r in db.get_relations(
            dest=input_node,
            type_=db.RELATION_TYPES.input_to_input
        ):
        r.delete()