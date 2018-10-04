import functools
import logging

from django.db import models
from django.utils import timezone

from .constants import *

try:
  basestring
except NameError:
  basestring = str


def isstring(x):
    return isinstance(x, basestring)


logger = logging.getLogger(__name__)


def retry_once(f):
    """ retry a callable once if return value evaluates to False
    """
    def wrapped(*args, **kwargs):
        if not f(*args, **kwargs):
            logger.warning("Retrying transition {}".format(f.__name__))
            if not f(*args, **kwargs):
                logger.error("Aborting transition {}".format(f.__name__))
    return wrapped


class StateField(models.Field):
    """
    StateField that renders as a CharField, with 'max_length', 'default' and optional 'choices'
    Params:
    max_length: will be overriden by the longest state length if necessary, defaults to 16
    choices: if True, will collect the states from all the subclasses of the mother class
             in the CharField's choices
    This class works in conjunction with class KWorkFlow
    CharField's 'default' will be set as the first state of all the subclasses (if it is the same,
      otherwise an exception is raised)
    """
    def __init__(self, *args, **kwargs):
        if args:
            workflow = args[0]
            args = args[1:]
            states = workflow.get_aggregated_states()
            l = max(len(s[0]) for s in states)
            max_length = max(kwargs.get('max_length', 16), len(CREATION_STATE))
            kwargs['max_length'] = max(max_length, l)
            if kwargs.pop('choices', False):
                kwargs['choices'] = states
            kwargs['default'] = workflow.get_aggregated_first_state()
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, 'models.CharField', args, kwargs


class KWorkFlow(object):
    """
    Base workflow class with a factory
    Usage: define your set of polymorphic workflows from a common mother class that you create this way:
    MyWorkflowFamilly = KWorkFlow.factory('MyWorkflowFamilly')
    """

    @classmethod
    def factory(cls, name):
        return type(name, (cls,), {'__module__': __name__})

    @classmethod
    def get_aggregated_states(cls):
        """ Called by mother class only
            return the tuple of aggregated states found in subclasses
        """
        states = {}
        for sc in cls.__subclasses__():
            states.update(dict(sc.states))
        return tuple((k, v) for k, v in states.items())

    @classmethod
    def get_aggregated_first_state(cls):
        """ Called by mother class only
            return common first state of all subclasses, raise if ambiguous
        """
        first_states = {sc.first_state() for sc in cls.__subclasses__()}
        if len(first_states) > 1:
            raise MultipleDifferentFirstStates(cls.__name__)
        return first_states.pop()

    @classmethod
    def first_state(cls):
        """ return first state of workflow (=initial state)
        """
        return cls.states[0][0]

    @classmethod
    def find_transition(cls, transition):
        """ find transition and return 'from' states and 'to' state,
            raise if transition not found
        """
        if not hasattr(cls, '_transitions'):
            # format data and do some sanity checks
            cls._states = {s[0] for s in cls.states}
            if len(cls.states) != len(cls._states):
                raise InconsistentStateList(cls.__name__)
            cls._transitions = {tr: ((fr,), to) if isstring(fr) else (fr, to) for tr, fr, to in cls.transitions}
            for tr, v in cls._transitions.items():
                if v[1] not in cls._states:
                    raise InconsistentStateInTransition(cls.__name__, tr, 'final')
                if len(set(v[0]).intersection(cls._states)) != len(v[0]):
                    raise InconsistentStateInTransition(cls.__name__, tr, 'start')
        try:
            return cls._transitions[transition]
        except KeyError:
            raise InvalidTransitionName(cls.__name__, transition)

    @classmethod
    def advance_state(cls, transition, state):
        """ find and return resulting state from current state and transition name,
            raise if wrong transition or wrong current state
        """
        t = cls.find_transition(transition)
        if state in t[0]:
            return t[1]
        raise InvalidStateForTransition(cls.__name__, transition, state)


class KWorkFlowEnabled(models.Model):
    workflow = None
    histo = None
    histo_create = True  # if False, creation step will not be historised
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
        if self.__class__.objects.filter(
            uid=self.uid,
            state_version=self.state_version
        ).update(
            modified_at=timezone.now(),
            state=self.workflow.advance_state(transition, self.state),
            state_version=self.state_version + 1
        ):
            self.refresh_from_db()
            if self.histo:
                self.histo.objects.create(from_state=old_state, to_state=self.state, underlying=self)
            return True


class WorkflowEnabledManager(models.Manager):
    """
    Manager for workflow enabled model
    """

    def create(self, **kwargs):
        if getattr(self.model._meta, 'proxy', None):
            for k, v in self.model.specific_fields.items():
                kwargs[k] = v() if callable(v) else v
        new = super().create(**kwargs)
        if self.model.histo and self.model.histo_create:
            self.model.histo.objects.create(from_state=CREATION_STATE,
                                            to_state=self.model.workflow.first_state(), underlying=new)
        return new


def transition(f):
    def wrapped(self, *args, **kwargs):
        self.workflow.find_transition(f.__name__)  # check transition name
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
