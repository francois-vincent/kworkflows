import random
from six.moves import range


UUID_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
UUID_ALPHABET_WITH_UPPERCASE = UUID_ALPHABET + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_id_with_prefix(prefix=None, length=8, with_uppercase=False):
    """Make a new id by joining randomly picked chars from alphabet, with optional prefix"""
    alphabet = UUID_ALPHABET_WITH_UPPERCASE if with_uppercase else UUID_ALPHABET
    rs = ''.join(random.choice(alphabet) for _ in range(length))
    return prefix + '_' + rs if prefix is not None else rs


def retry_once(f):
    """ retry a callable once if return value evaluates to False
    """
    def wrapped(*args, **kwargs):
        if not f(*args, **kwargs):
            f(*args, **kwargs)
    return wrapped
