
from django.models import ChoiceField

from .utils import make_id_with_prefix


class StateField(ChoiceField):
    pass


class KWorkFlow(object):
    """ Root workflow class with a factory
    """

    @classmethod
    def factory(cls, name=None):
        return type(name or make_id_with_prefix(cls.__name__), (cls,), {'__module__': __name__})


class KWorkFlowEnabled(object):
    pass
