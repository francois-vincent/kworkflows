import functools

from django.db import models

from .constants import *
from .utils import make_id_with_prefix


class UIDField(models.Field):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 8)
        kwargs.setdefault('default', functools.partial(make_id_with_prefix, length=kwargs['max_length']))
        kwargs.setdefault('unique', True)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, 'models.CharField', args, kwargs


class StateField(models.Field):
    def __init__(self, *args, **kwargs):
        if args:
            workflow = args[0]
            args = args[1:]
            states = workflow.get_states()
            l = max(len(s[0]) for s in states)
            max_length = kwargs.get('max_length', 20)
            kwargs['max_length'] = max(max_length, l)
            kwargs['choices'] = states
            kwargs['default'] = workflow.get_first_state()
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, 'models.CharField', args, kwargs


class KWorkFlow(object):
    """ Root workflow class with a factory
    """

    @classmethod
    def factory(cls, name=None):
        return type(name or make_id_with_prefix(cls.__name__), (cls,), {'__module__': __name__})

    @classmethod
    def get_states(cls):
        states = {}
        for sc in cls.__subclasses__():
            states.update(dict(sc.states))
        return tuple((k, v) for k, v in states.items())

    @classmethod
    def get_first_state(cls):
        first_states = {sc.states[0][0] for sc in cls.__subclasses__()}
        if len(first_states) > 1:
            raise MultipleDifferentFirstStates(cls.__name__)
        return first_states.pop()

    @classmethod
    def find_transition(cls, transition):
        for t in cls.transitions:
            if transition == t[0]:
                return t
        raise InvalidTransitionName(cls.__name__, transition)

    @classmethod
    def advance_state(cls, transition, state):
        t = cls.find_transition(transition)
        if state == t[1] or state in t[1]:
            return t[2]
        raise InvalidStateForTransition(cls.__name__, transition, state)


class KWorkFlowEnabled(object):
    workflow = None
    pre_transitions = {}
    post_transitions = {}

    def advance_state(self, transition):
        self.state = self.workflow.advance_state(transition, self.state)
        self.save()
