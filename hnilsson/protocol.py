import irken
import simplejson
from irken.base import RemoteSource, BaseConnection
from irken.nicks import Mask
from irken.dispatch import Command

class JSONEncoder(simplejson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (RemoteSource, BaseConnection)):
            if not obj.mask:
                return None
            return obj.mask.to_string()
        return super(JSONEncoder, self).default(obj)

class Job(tuple):
    make_mask = Mask.from_string

    def __new__(cls, cmd, args=(), kwds={}):
        return super(Job, cls).__new__(cls, (cmd, tuple(args), kwds))

    def __init__(self, cmd, args=(), kwds={}):
        super(Job, self).__init__((cmd, tuple(args), kwds))

    def as_str(self):
        r"""Turn a job into the protocol-level representation.

        >>> job_str("HELLO", "foo", "bar", quux=1)
        '[[null, "HELLO"], ["foo", "bar"], {"quux": 1}]\n'

        Slightly more real and complicated case:

        >>> from irken.nicks import Mask
        >>> from irken.base import RemoteSource
        >>> from irken.dispatch import Command
        >>> source = RemoteSource(Mask.from_string("hello"))
        >>> job_str((source, "TEST"), "blah", tengil=1337)
        '[["hello", "TEST"], ["blah"], {"tengil": 1337}]\n'
        """
        return simplejson.dumps(tuple(self), cls=JSONEncoder)

    @classmethod
    def from_str(cls, job_data):
        (prefix, name), args, kwds = simplejson.loads(job_data)
        source = prefix
        if prefix:
            source = cls.make_mask(prefix)
        return cls((source, name), args, kwds)
