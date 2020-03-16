from Jumpscale import j

import struct
import builtins
from .TypeBaseClassesObj import *


class TypeBaseObjClassNumeric(TypeBaseObjClass):
    @property
    def _value(self):
        raise j.exceptions.NotImplemented()

    # def __eq__(self, other):
    #     n = self._typebase.clean(other)
    #     return self._value == n.value

    def __gt__(self, other):
        n = self._typebase.clean(other)
        return self._value > n.value

    def __ge__(self, other):
        n = self._typebase.clean(other)
        return self._value >= n.value

    def __lt__(self, other):
        n = self._typebase.clean(other)
        return self._value < n.value

    def __le__(self, other):
        n = self._typebase.clean(other)
        return self._value <= n.value

    # def __add__(self, other):
    #     n = self._typebase.clean(other)
    #     r = self._value + n.value
    #     return self._typebase.clean(r)
    #
    # def __sub__(self, other):
    #     n = self._typebase.clean(other)
    #     r = self._value - n.value
    #     return self._typebase.clean(r)
    #
    # def __mul__(self, other):
    #     n = self._typebase.clean(other)
    #     r = self._value * n.value
    #     return self._typebase.clean(r)
    #
    # def __div__(self, other):
    #     n = self._typebase.clean(other)
    #     r = self._value / n.value
    #     return self._typebase.clean(r)

    def __hash__(self):
        return hash(self._value)

    def __eq__(self, other):
        other = self._typebase.clean(other)
        return float(other) == float(self)

    def __bool__(self):
        return self._data is not None

    def _other_convert(self, other):
        return self._typebase.clean(other)

    def __add__(self, other):
        other = self._other_convert(other)
        return self._typebase.clean(float(other) + float(self))

    def __iadd__(self, other):
        other = self._other_convert(other)
        self._value = float(self) + float(other)
        return self

    def __sub__(self, other):
        other = self._other_convert(other)
        return self._typebase.clean(float(self) - float(other))

    def __mul__(self, other):
        other = self._other_convert(other)
        return self._typebase.clean(float(self) * float(other))

    def __matmul__(self, other):
        other = self._other_convert(other)
        return self._typebase.clean(float(self) @ float(other))

    def __truediv__(self, other):
        other = self._other_convert(other)
        return self._typebase.clean(float(self) / float(other))

    def __floordiv__(self, other):
        other = self._other_convert(other)
        return self._typebase.clean(float(self) // float(other))

    def __mod__(self, other):
        raise NotImplemented()

    def __divmod__(self, other):
        raise NotImplemented()

    def __pow__(self, other):
        raise NotImplemented()

    def __lshift__(self):
        raise NotImplemented()

    def __neg__(self):
        return self._typebase.clean(float(self) * -1)

    def __float__(self):
        return float(self._value)

    def __int__(self):
        return int(self._value)

    __rshift__ = __lshift__
    __and__ = __lshift__
    __xor__ = __lshift__
    __or__ = __lshift__


class NumericObject(TypeBaseObjClassNumeric):
    @property
    def _string(self):
        return self._typebase.bytes2str(self._data)

    @property
    def _python_code(self):
        return "'%s'" % self._string

    @property
    def usd(self):
        return self.value

    @property
    def _value(self):
        return self._typebase.bytes2cur(self._data)

    @value.setter
    def _value(self, val):
        self._data = self._typebase.toData(val)

    @property
    def currency_code(self):
        curcode, val = self._typebase.bytes2cur(self._data, return_currency_code=True)
        return curcode

    def value_currency(self, curcode="usd"):
        return self._typebase.bytes2cur(self._data, curcode=curcode)

    def __str__(self):
        if self._data:
            return self._string
        else:
            return "numeric: NOTSET"

    __repr__ = __str__


class Numeric(TypeBaseObjClassFactory):
    """
    has support for currencies and does nice formatting in string

    storformat = 6 or 10 bytes (10 for float)

    will return int as jumpscale basic implementation

    """

    NAME = "numeric,n"

    def __init__(self, default=None):
        TypeBaseObjClassFactory.__init__(self)
        self.BASETYPE = "bytes"
        self.NOCHECK = True
        self._default = default

    def bytes2cur(self, bindata, curcode="usd", roundnr=None, return_currency_code=False):

        if bindata in [b"", None]:
            return 0

        if len(bindata) not in [6, 10]:
            raise j.exceptions.Input("len of data needs to be 6 or 10")

        ttype = struct.unpack("B", builtins.bytes([bindata[0]]))[0]
        curtype0 = struct.unpack("B", builtins.bytes([bindata[1]]))[0]

        if ttype > 127:
            ttype = ttype - 128
            negative = True
        else:
            negative = False

        if ttype == 1:
            val = struct.unpack("d", bindata[2:])[0]
        else:
            val = struct.unpack("I", bindata[2:])[0]

        if ttype == 10:
            val = val * 1000
        elif ttype == 11:
            val = val * 1000000
        elif ttype == 2:
            val = round(float(val) / 10000, 3)
            if int(float(val)) == val:
                val = int(val)

        # if curtype0 not in j.clients.currencylayer.id2cur:
        #     raise j.exceptions.Value("need to specify valid curtype, was:%s"%curtype)
        currency = j.clients.currencylayer
        curcode0 = currency.id2cur[curtype0]
        if not curcode0 == curcode:
            val = val / currency.cur2usd[curcode0]  # val now in usd
            val = val * currency.cur2usd[curcode]

        if negative:
            val = -val

        if val > 80 and not roundnr:
            roundnr = 0

        if roundnr:
            val = round(val, roundnr)

        if return_currency_code:
            return curcode0, val
        else:
            return val

    def bytes2str(self, bindata, roundnr=None, comma=True):
        if len(bindata) == 0:
            bindata = self.default_get()

        elif len(bindata) not in [6, 10]:
            raise j.exceptions.Input("len of data needs to be 6 or 10")

        ttype = struct.unpack("B", builtins.bytes([bindata[0]]))[0]
        curtype = struct.unpack("B", builtins.bytes([bindata[1]]))[0]

        if ttype > 127:
            ttype = ttype - 128
            negative = True
        else:
            negative = False

        if ttype == 1:
            val = struct.unpack("d", bindata[2:])[0]
        else:
            val = struct.unpack("I", bindata[2:])[0]

        if ttype == 10:
            mult = "k"
        elif ttype == 11:
            mult = "m"
        elif ttype == 2:
            mult = "%"
            val = round(float(val) / 100, 2)
            if int(val) == val:
                val = int(val)
        else:
            mult = ""
        currency = j.clients.currencylayer
        if curtype is not currency.cur2id["usd"]:
            curcode = currency.id2cur[curtype]
        else:
            curcode = ""

        if not roundnr:
            if val > 100:
                roundnr = 0
            elif val > 10:
                roundnr = 1

        if roundnr == 0:
            val = int(val)
        elif roundnr:
            val = round(val, roundnr)

        if comma:
            out = str(val)
            if "." not in out:
                val = ""
                while len(out) > 3:
                    val = "," + out[-3:] + val
                    out = out[:-3]
                val = out + val
                val = val.strip(",")

        if negative:
            res = "-%s %s%s" % (val, mult, curcode.upper())
        else:
            res = "%s %s%s" % (val, mult, curcode.upper())
        res = res.replace(" %", "%")
        # print(res)
        return res.strip()

    def getCur(self, value):
        value = value.lower()
        for cur2 in list(j.clients.currencylayer.cur2id):
            # print(cur2)
            if value.find(cur2) != -1:
                # print("FOUND:%s"%cur2)
                value = value.lower().replace(cur2, "").strip()
                return value, cur2
        cur2 = "usd"
        return value, cur2

    def str2bytes(self, value):
        """

        US style: , is for 1000  dot(.) is for floats

        value can be 10%,0.1,100,1m,1k  m=million
        USD/EUR/CH/EGP/GBP are understood (+- all currencies in world)

        e.g.: 10%
        e.g.: 10EUR or 10 EUR (spaces are stripped)
        e.g.: 0.1mEUR or 0.1m EUR or 100k EUR or 100000 EUR

        j.tools.numtools.text2num_bytes("0.1mEUR")

        j.tools.numtools.text2num_bytes("100")
        if not currency symbol specified then will default to usd

        bytes format:

        $type:1byte + $cur:1byte + $4byte value (int or float)

        $type:
        last 4 bytes:
        - 0: int, no multiplier
        - 1: float, no multiplier
        - 2: int, percent (expressed as 1-10000, so 100% = 10000, 1%=100)
        - 3: was float but expressed as int because is bigger than 10000 (no need to keep float part)
        - 10: int, multiplier = 1000
        - 11: int, multiplier = 1000000

        first bit:
        - True if neg nr, otherwise pos nr (in other words if nr < 128 then pos nr)

        see for codes in:
        - j.clients.currencylayer.cur2id
        - j.clients.currencylayer.id2cur

        """

        if not j.data.types.string.check(value):
            raise j.exceptions.RuntimeError("value needs to be string in text2val, here: %s" % value)

        if "," in value:  # is only formatting in US
            value = value.replace(",", "").lstrip(",").strip()

        if "-" in value:
            negative = True
            value = value.replace("-", "").lstrip("-")
        else:
            negative = False

        try:
            # dirty trick to see if value can be float, if not will look for currencies
            v = float(value)
            cur2 = "usd"
        except ValueError as e:
            cur2 = None

        if cur2 is None:
            value, cur2 = self.getCur(value)

        if value.find("k") != -1:
            value = value.replace("k", "").strip()
            if "." in value:
                value = int(float(value) * 1000)
                ttype = 0
            else:
                value = int(value)
                ttype = 10
        elif value.find("m") != -1:
            value = value.replace("m", "").strip()
            if "." in value:
                value = int(float(value) * 1000)
                ttype = 10
            else:
                value = int(value)
                ttype = 11
        elif value.find("%") != -1:
            value = value.replace("%", "").strip()
            value = int(float(value) * 100)
            ttype = 2
        else:
            if value.strip() == "":
                value = "0"
            fv = float(value)
            if fv.is_integer():  # check floated val fits into an int
                # ok, we now know str->float->int will actually be an int
                value = int(fv)
                ttype = 0
            else:
                value = fv
                if fv > 10000:
                    value = int(value)  # doesn't look safe.  issue #72
                    ttype = 3
                else:
                    ttype = 1
        currency = j.clients.currencylayer
        curcat = currency.cur2id[cur2]

        if negative:
            ttype += 128

        if ttype == 1 or ttype == 129:
            return struct.pack("B", ttype) + struct.pack("B", curcat) + struct.pack("d", value)
        else:
            return struct.pack("B", ttype) + struct.pack("B", curcat) + struct.pack("I", value)

    def clean(self, data=None, parent=None):
        if isinstance(data, NumericObject):
            return data
        if data is None or data == "None" or data == b"" or data == "":
            return self.default_get()
        if isinstance(data, float) or isinstance(data, int):
            data = str(data)
        if isinstance(data, str):
            data = self.str2bytes(data)
        if isinstance(data, bytes):
            return NumericObject(self, data)
        else:
            # j.debug()
            raise j.exceptions.Value("was not able to clean numeric : %s" % data)

    def toData(self, data):
        data = self.clean(data)
        return data._data

    #     # print("num:clean:%s"%data)
    #     if j.data.types.string.check(data):
    #         data = j.data.types.string.clean(data)
    #         data = self.str2bytes(data)
    #     elif j.data.types.bytes.check(data):
    #         if len(data) not in [6, 10]:
    #             raise j.exceptions.Input("len of numeric bytes needs to be 6 or 10 bytes")
    #     elif isinstance(data,int) or isinstance(data,float):
    #         data = self.str2bytes(str(data))
    #     else:
    #         j.shell()
    #         raise j.exceptions.Value("could not clean data, did not find supported type:%s"%data)
    #
    #     return data

    def default_get(self):
        if not self._default:
            self._default = 0
        return self.clean(self._default)
