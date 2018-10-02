import functools

from django.db import models

from .constants import *
from .utils import make_id_with_prefix, retry_once


class UIDField(models.Field):
    """ A auto fill UIDField that renders as a simple CharField,
        with >4e18 combinations
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 12)
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
            max_length = kwargs.get('max_length', 16)
            kwargs['max_length'] = max(max_length, l)
            if kwargs.pop('choices', False):
                kwargs['choices'] = states
            kwargs['default'] = workflow.get_first_state()
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, 'models.CharField', args, kwargs


class KWorkFlow(object):
    """ Base workflow class with a factory
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


class KWorkFlowEnabled(models.Model):
    workflow = None
    histo = None
    state_version = models.IntegerField(default=0)  # this is used for optimistic concurrency management

    class Meta:
        abstract = True

    def advance_state(self, transition):
        self.state = self.workflow.advance_state(transition, self.state)
        return self.state

    @retry_once
    def safe_advance_state(self, transition):
        """ safe means using optimistic concurrency management
        see https://medium.com/@hakibenita/how-to-manage-concurrency-in-django-models-b240fed4ee2
        :param transition: the name of the transition to perform
        :return: true if transition successfull
        """
        old_state = self.state
        success = self.__class__.objects.filter(
            uid=self.uid,
            state_version=self.state_version
        ).update(
            state=self.workflow.advance_state(transition, self.state),
            state_version=self.state_version + 1
        ) > 0
        if success:
            self.refresh_from_db()
            if self.histo:
                self.histo.objects.create(from_state=old_state, to_state=self.state, underlying=self)
        return success


def transition(f):
    def wrapped(self, *args, **kwargs):
        self.workflow.find_transition(f.__name__)
        return f(self, functools.partial(self.safe_advance_state, f.__name__), *args, **kwargs)
    return wrapped


class WorkFlowHistory(models.Model):
    timestamp = models.DateTimeField(auto_now=True)
    from_state = models.CharField(max_length=20)
    to_state = models.CharField(max_length=20)

    class Meta:
        abstract = True
        ordering = ['timestamp']
        get_latest_by = 'timestamp'
