# TODO" NOT READY TO BE USED, see despiegk

from Jumpscale import j
from Jumpscale.data.types.TypeBaseClasses import TypeBaseObjFactory, TypeBaseObjClass


class DMBase(TypeBaseObjClass):
    def __init__(self, typebase, value=None):

        self.BASETYPE = "bytes"

        self._typebase = typebase  # is the factory for this object

        if value is None:
            self._data = None
        else:
            self._data = self._typebase.toData(value)  # returns the native lowest level type


class DM(DMBase):
    def __init__(self, typebase, value=None):

        TypeBaseObjClass.__init__(self, typebase, value)

        self._id = None
        self._hid = None
        self._pubkey = None
        self._addr = None

    def _capnp_schema_get(self, name, nr):
        return self._typebase.capnp_schema_get(name, nr)

    @property
    def _string(self):
        v = self.value
        if v["id"] == 0:
            return "UNKNOWN"
        else:
            return v["hid"]

    @property
    def _exists(self):
        res = j.core.db.hget("dm:id", self._data)
        return not res is None

    @property
    def _python_code(self):
        return "'%s'" % self._string

    @property
    def _datadict(self):
        return self._data

    def _encode(self, ddict):
        r = []
        r.append(self.id)
        r.append(self.hid)
        r.append(self.pubkey)
        r.append(self.addr)
        return j.data.serializers.msgpack.dumps(r)

    def _decode(self, bin):
        res = {}
        r = j.data.serializers.msgpack.loads(bin)
        res["id"] = r[0]
        res["hid"] = r[1]
        res["pubkey"] = r[2]
        res["addr"] = r[3]
        return res

    @property
    def value(self):
        # check if it exists in redis (cache), if not retrieve from remote DM
        res = j.core.db.hget("dm:id", self._data)
        if res is None:
            pass  # TODO: *1 need to fetch from blockchain, only if not there need to return default
            return self._default
        else:
            return self._decode(res)

    def __str__(self):
        if self._data:
            return "%s: %s" % (self._typebase.__class__.NAME, self._string)
        else:
            return "%s: NOTSET" % (self._typebase.__class__.NAME)

    __repr__ = __str__


class DMTypeFactory(TypeBaseObjFactory):
    """
    each digitalme has a unique id of max 4 bytes,
    this is registered in the blockchain

    0 is reserved for the nonexist (null) Digital ME
    """

    def __init__(self):
        self.BASETYPE = "integer"
        self.NAME = "dmid"  # DIGITAL ME ID

    def default_get(self):
        return self.clean(0)

    def check(self, value):
        if isinstance(value, DMID):
            return True

    def toString(self, val):
        val = self.clean(val)
        return val._string

    def toData(self, v):
        raise j.exceptions.NotImplemented()

    def clean(self, v):
        if value is None:
            return self.default_get()
        raise j.exceptions.NotImplemented()
