from solar.core import signals
from solar.interfaces.db import get_db

db = get_db()


class BaseObserver(object):
    type_ = None

    def __init__(self, attached_to, name, value):
        """
        :param attached_to: resource.Resource
        :param name:
        :param value:
        :return:
        """
        self._attached_to_name = attached_to.name
        self.name = name
        self.value = value

    @property
    def attached_to(self):
        from solar.core import resource

        return resource.load(self._attached_to_name)

    @property
    def receivers(self):
        from solar.core import resource

        signals.CLIENTS = signals.Connections.read_clients()
        for receiver_name, receiver_input in signals.Connections.receivers(
                    self._attached_to_name,
                    self.name
                ):
            yield resource.load(receiver_name).args[receiver_input]

    def log(self, msg):
        print '{} {}'.format(self, msg)

    def __repr__(self):
        return '[{}:{}] {}'.format(self._attached_to_name, self.name, self.value)

    def __unicode__(self):
        return unicode(self.value)

    def __eq__(self, other):
        if isinstance(other, BaseObserver):
            return self.value == other.value

        return self.value == other

    def notify(self, emitter):
        """
        :param emitter: Observer
        :return:
        """
        raise NotImplementedError

    def update(self, value):
        """
        :param value:
        :return:
        """
        raise NotImplementedError

    def find_receiver(self, receiver):
        fltr = [r for r in self.receivers
                if r._attached_to_name == receiver._attached_to_name
                and r.name == receiver.name]
        if fltr:
            return fltr[0]

    def subscribe(self, receiver):
        """
        :param receiver: Observer
        :return:
        """
        self.log('Subscribe {}'.format(receiver))
        # No multiple subscriptions
        if self.find_receiver(receiver):
            self.log('No multiple subscriptions from {}'.format(receiver))
            return
        receiver.subscribed(self)

        signals.Connections.add(
            self.attached_to,
            self.name,
            receiver.attached_to,
            receiver.name
        )

        receiver.notify(self)

    def subscribed(self, emitter):
        self.log('Subscribed {}'.format(emitter))

    def unsubscribe(self, receiver):
        """
        :param receiver: Observer
        :return:
        """
        self.log('Unsubscribe {}'.format(receiver))
        if self.find_receiver(receiver):
            receiver.unsubscribed(self)

        signals.Connections.remove(
            self.attached_to,
            self.name,
            receiver.attached_to,
            receiver.name
        )

        # TODO: ?
        #receiver.notify(self)

    def unsubscribed(self, emitter):
        self.log('Unsubscribed {}'.format(emitter))


class Observer(BaseObserver):
    type_ = 'simple'

    @property
    def emitter(self):
        from solar.core import resource

        emitter = signals.Connections.emitter(self._attached_to_name, self.name)

        if emitter is not None:
            emitter_name, emitter_input_name = emitter
            return resource.load(emitter_name).args[emitter_input_name]

    def notify(self, emitter):
        self.log('Notify from {} value {}'.format(emitter, emitter.value))
        # Copy emitter's values to receiver
        self.value = emitter.value
        for receiver in self.receivers:
            receiver.notify(self)
        self.attached_to.set_args_from_dict({self.name: self.value})

    def update(self, value):
        self.log('Updating to value {}'.format(value))
        self.value = value
        for receiver in self.receivers:
            receiver.notify(self)
        self.attached_to.set_args_from_dict({self.name: self.value})

    def subscribed(self, emitter):
        super(Observer, self).subscribed(emitter)
        # Simple observer can be attached to at most one emitter
        if self.emitter is not None:
            self.emitter.unsubscribe(self)


class ListObserver(BaseObserver):
    type_ = 'list'

    def __unicode__(self):
        return unicode(self.value)

    @staticmethod
    def _format_value(emitter):
        return {
            'emitter': emitter.name,
            'emitter_attached_to': emitter._attached_to_name,
            'value': emitter.value,
        }

    def notify(self, emitter):
        self.log('Notify from {} value {}'.format(emitter, emitter.value))
        # Copy emitter's values to receiver
        idx = self._emitter_idx(emitter)
        self.value[idx] = self._format_value(emitter)
        for receiver in self.receivers:
            receiver.notify(self)
        self.attached_to.set_args_from_dict({self.name: self.value})

    def subscribed(self, emitter):
        super(ListObserver, self).subscribed(emitter)
        idx = self._emitter_idx(emitter)
        if idx is None:
            self.value.append(self._format_value(emitter))
        self.attached_to.set_args_from_dict({self.name: self.value})

    def unsubscribed(self, emitter):
        """
        :param receiver: Observer
        :return:
        """
        self.log('Unsubscribed emitter {}'.format(emitter))
        idx = self._emitter_idx(emitter)
        self.value.pop(idx)
        self.attached_to.set_args_from_dict({self.name: self.value})
        for receiver in self.receivers:
            receiver.notify(self)

    def _emitter_idx(self, emitter):
        try:
            return [i for i, e in enumerate(self.value)
                    if e['emitter_attached_to'] == emitter._attached_to_name
                    ][0]
        except IndexError:
            return


def create(type_, *args, **kwargs):
    for klass in BaseObserver.__subclasses__():
        if klass.type_ == type_:
            return klass(*args, **kwargs)
    raise NotImplementedError('No handling class for type {}'.format(type_))
