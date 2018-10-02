import functools
import random
from six.moves import range

from django.db import models


UUID_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
UUID_ALPHABET_WITH_UPPERCASE = UUID_ALPHABET + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_id_with_prefix(prefix=None, length=8, with_uppercase=False):
    """Make a new id by joining randomly picked chars from alphabet, with optional prefix"""
    alphabet = UUID_ALPHABET_WITH_UPPERCASE if with_uppercase else UUID_ALPHABET
    rs = ''.join(random.choice(alphabet) for _ in range(length))
    return prefix + '_' + rs if prefix is not None else rs


class UIDField(models.Field):
    """ A auto fill UIDField that renders as a simple CharField,
        with 36**12 >4e18 combinations
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 12)
        kwargs.setdefault('default', functools.partial(make_id_with_prefix, length=kwargs['max_length']))
        kwargs.setdefault('unique', True)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, 'models.CharField', args, kwargs
