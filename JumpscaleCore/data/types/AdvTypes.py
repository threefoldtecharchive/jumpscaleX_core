""" Definition of several custom types (paths, ipaddress, guid,...)
"""

import re
import struct
import builtins
from .PrimitiveTypes import String, Integer
from functools import reduce
import copy
import time
from uuid import UUID
from Jumpscale import j
from datetime import datetime, timedelta
from .TypeBaseClasses import *


class Guid(String):
    """
    Generic GUID type
    stored as binary internally
    """

    NAME = "guid"

    def __init__(self, default=None):
        self.BASETYPE = "string"
        self._default = default

    def clean(self, value):
        if value is None or value == "":
            return self.default_get()
        if not self.check(value):
            raise j.exceptions.Value("invalid guid :%s" % value)
        else:
            return value

    def check(self, value):
        try:
            val = UUID(value, version=4)
        except (ValueError, AttributeError):
            return False
        return val.hex == value.replace("-", "")

    def default_get(self):
        if self._default:
            return self.clean(self._default)
        return j.data.idgenerator.generateGUID()

    def fromString(self, v):
        if not j.data.types.string.check(v):
            raise j.exceptions.Value("Input needs to be string:%s" % v)
        if self.check(v):
            return v
        else:
            raise j.exceptions.Value("%s not properly formatted: '%s'" % (Guid.NAME, v))

    toString = fromString


class Email(String):
    """
    """

    NAME = "email"

    def __init__(self, default=None):
        self.BASETYPE = "string"
        self._RE = re.compile("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        self._default = default

    def check(self, value):
        """
        Check whether provided value is a valid tel nr
        """
        if not j.data.types.string.check(value):
            return False
        if value.strip() == "":
            return True
        return self._RE.fullmatch(value) is not None

    def default_get(self):
        if self._default:
            return self.clean(self._default)
        return ""

    def clean(self, v):
        if isinstance(v, Email):
            return v
        if v is None or v == "None":
            return self.default_get()
        v = j.data.types.string.clean(v)
        if not self.check(v):
            raise j.exceptions.Value("Invalid email :%s" % v)
        v = v.lower()
        return v


class Path(String):
    """Generic path type"""

    NAME = "path"

    def __init__(self, default=None):
        self.BASETYPE = "string"
        self._RE = re.compile("^(?:\.{2})?(?:\/\.{2})*(\/[a-zA-Z0-9]+)+$")
        self._default = default

    def check(self, value):
        """
        Check whether provided value is a valid
        """
        return self._RE.fullmatch(value) is not None

    def default_get(self):
        return ""


class Url(String):
    """Generic url type"""

    NAME = "url,u"

    def __init__(self, default=None):
        self.BASETYPE = "string"
        self._RE = re.compile(
            "(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9]\.[^\s]{2,}"
        )
        self._default = default

    def clean(self, value):
        if value is None or value == "None" or value == "":
            return self.default_get()
        if not self.check(value):
            raise j.exceptions.Value("invalid url :%s" % value)
        else:
            return value

    def check(self, value):
        """
        Check whether provided value is a valid
        """
        return self._RE.fullmatch(value) is not None


class Tel(String):
    """
    format is e.g. +32 475.99.99.99x123
    only requirement is it needs to start with +
    the. & , and spaces will not be remembered
    and x stands for phone number extension
    """

    NAME = "tel,mobile"

    def __init__(self, default=None):
        self.BASETYPE = "string"
        self._RE = re.compile("^\+?[0-9]{6,15}(?:x[0-9]+)?$")
        self._default = default

    def check(self, value):
        """
        Check whether provided value is a valid
        """
        if not value:
            return True
        return self._RE.fullmatch(value) is not None

    def clean(self, v):
        if v is None or v == "None":
            return self.default_get()
        v = j.data.types.string.clean(v)
        v = v.replace(",", "")
        v = v.replace("-", "")
        v = v.replace("(", "")
        v = v.replace(")", "")
        v = v.replace(" ", "")
        if not self.check(v):
            raise j.exceptions.Value("Invalid mobile number :%s" % v)
        return v

    def default_get(self):
        if not self._default:
            self._default = None
        return self._default


class IPRange(String):
    """
    """

    NAME = "iprange"

    def __init__(self, default=None):
        self.BASETYPE = "string"
        self._RE = re.compile("[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[0-9]{1,2}")
        self._default = default

    def check(self, value):
        """
        Check whether provided value is a valid
        """
        return self._RE.fullmatch(value) is not None

    def clean(self, value):

        if value is None or value == "None" or value == "":
            return self.default_get()
        if not self.check(value):
            raise j.exceptions.Value("invalid ip range %s" % value)
        else:
            return value


class IPPort(Integer):
    """Generic IP port type"""

    NAME = "ipport,tcpport"

    def __init__(self, default=None):
        self.BASETYPE = "int"
        self.NOCHECK = True
        # j.shell()
        self._default = default

    def default_get(self):
        if not self._default:
            self._default = 65535
        return self._default

    def possible(self, value):
        """
        Check if the value is a valid port
        We just check if the value a single port or a range
        Values must be between 0 and 65535
        """
        try:
            if 0 < int(value) <= 65535:
                return True
        except:
            pass
        return False

    def clean(self, value):
        if not value:
            return self.default_get()
        if not self.check(value):
            raise j.exceptions.Value("invalid port: %s" % value)
        else:
            return int(value)

    def check(self, value):
        return self.possible(value)

    def toHR(self, v):
        if int(v) == 65535:
            return "-"  # means not set yet
        return self.clean(v)


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
    def value(self):
        return self._typebase.bytes2cur(self._data)

    @value.setter
    def value(self, val):
        self._data = self._typebase.toData(val)

    @property
    def currency_code(self):
        curcode, val = self._typebase.bytes2cur(self._data, return_currency_code=True)
        return curcode

    def value_currency(self, curcode="usd"):
        return self._typebase.bytes2cur(self._data, curcode=curcode)

    def __str__(self):
        if self._data:
            return "numeric (%s): %s" % (self.value_currency, self._string)
        else:
            return "numeric: NOTSET"


class Numeric(TypeBaseObjFactory):
    """
    has support for currencies and does nice formatting in string

    storformat = 6 or 10 bytes (10 for float)

    will return int as jumpscale basic implementation

    """

    NAME = "numeric,n"

    def __init__(self, default=None):
        TypeBaseObjFactory.__init__(self)
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

        if roundnr:
            val = round(val, roundnr)

        if return_currency_code:
            return curcode0, val
        else:
            return val

    def bytes2str(self, bindata, roundnr=8, comma=True):
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

    def clean(self, data=None):
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


class DateTime(Integer):
    """
    internal representation is an epoch (int)
    """

    NAME = "datetime,t"

    def __init__(self, default=None):

        self.BASETYPE = "int"
        self.NOCHECK = True
        self._default = default

        # self._RE = re.compile('[0-9]{4}/[0-9]{2}/[0-9]{2}')  #something wrong here is not valid for time

    def default_get(self):
        if not self._default:
            self._default = 0
        return self._default

    def fromString(self, txt):
        return self.clean(txt)

    def toString(self, val, local=True):
        val = self.clean(val)
        if val == 0:
            return ""
        return j.data.time.epoch2HRDateTime(val, local=local)

    def toHR(self, v):
        return self.toString(v)

    def clean(self, v):
        """
        support following formats:
        - None, 0: means undefined date
        - epoch = int
        - month/day 22:50
        - month/day  (will be current year if specified this way)
        - year(4char)/month/day
        - year(4char)/month/day 10am:50
        - year(2char)/month/day
        - day/month/4char
        - year(4char)/month/day 22:50
        - +4h
        - -4h
        in stead of h also supported: s (second) ,m (min) ,h (hour) ,d (day),w (week), M (month), Y (year)

        will return epoch

        """
        if v is None:
            return self.default_get()

        def date_process(dd):
            if "/" not in dd:
                raise j.exceptions.Input("date needs to have:/, now:%s" % v)
            splitted = dd.split("/")
            if len(splitted) == 2:
                dfstr = "%Y/%m/%d"
                dd = "%s/%s" % (j.data.time.epoch2HRDate(j.data.time.epoch).split("/")[0], dd.strip())
            elif len(splitted) == 3:
                s0 = splitted[0].strip()
                s1 = splitted[1].strip()
                s2 = splitted[2].strip()
                if len(s0) == 4 and (len(s1) == 2 or len(s1) == 1) and (len(s2) == 2 or len(s2) == 1):
                    # year in front
                    dfstr = "%Y/%m/%d"
                elif len(s2) == 4 and (len(s1) == 2 or len(s1) == 1) and (len(s0) == 2 or len(s0) == 1):
                    # year at end
                    dfstr = "%d/%m/%Y"
                elif (
                    (len(s2) == 2 or len(s2) == 1) and (len(s1) == 2 or len(s1) == 1) and (len(s0) == 2 or len(s0) == 1)
                ):
                    # year at start but small
                    dfstr = "%y/%m/%d"
                else:
                    raise j.exceptions.Input("date wrongly formatted, now:%s" % v)
            else:
                raise j.exceptions.Input("date needs to have 2 or 3 /, now:%s" % v)
            return (dd, dfstr)

        def time_process(v):
            v = v.strip()
            if ":" not in v:
                return ("00:00:00", "%H:%M:%S")
            splitted = v.split(":")
            if len(splitted) == 2:
                if "am" in v.lower() or "pm" in v.lower():
                    fstr = "%I%p:%M"
                else:
                    fstr = "%H:%M"
            elif len(splitted) == 3:
                if "am" in v.lower() or "pm" in v.lower():
                    fstr = "%I%p:%M:%S"
                else:
                    fstr = "%H:%M:%S"
            return (v, fstr)

        if v is None:
            v = 0

        if j.data.types.int.check(v):
            return v
        elif j.data.types.int.checkString(v):
            v = int(v)
            return v
        elif j.data.types.string.check(v):
            v = v.replace("'", "").replace('"', "").strip()
            if v.strip() in ["0", "", 0]:
                return 0

            if "+" in v or "-" in v:
                return j.data.time.getEpochDeltaTime(v)

            if ":" in v:
                # have time inside the representation
                dd, tt = v.split(" ", 1)
                tt, tfstr = time_process(tt)
            else:
                tt, tfstr = time_process("")
                dd = v

            dd, dfstr = date_process(dd)

            fstr = dfstr + " " + tfstr
            hrdatetime = dd + " " + tt
            epoch = int(time.mktime(time.strptime(hrdatetime, fstr)))
            return epoch
        else:
            raise j.exceptions.Value("Input needs to be string:%s" % v)

    def capnp_schema_get(self, name, nr):
        return "%s @%s :UInt32;" % (name, nr)

    def test(self):
        """
        kosmos 'j.data.types.datetime.test()'
        """


class Date(DateTime):
    """
    internal representation is an epoch (int)
    """

    NAME = "date,d"

    def __init__(self, default=None):

        self.BASETYPE = "int"
        # self._RE = re.compile('[0-9]{4}/[0-9]{2}/[0-9]{2}')
        self.NOCHECK = True
        self._default = default

    def clean(self, v):
        """
        support following formats:
        - 0: means undefined date
        - epoch = int  (will round to start of the day = 00h)
        - month/day  (will be current year if specified this way)
        - year(4char)/month/day
        - year(2char)/month/day
        - day/month/4char
        - +4M
        - -4Y
        in stead of h also supported: s (second) ,m (min) ,h (hour) ,d (day),w (week), M (month), Y (year)

        will return epoch

        """
        if v is None:
            return self.default_get()
        if isinstance(v, str):
            v = v.replace("'", "").replace('"', "").strip()
        if v in [0, "0", None, ""]:
            return 0
        # am sure there are better ways how to do this but goes to beginning of day
        v2 = DateTime.clean(self, v)
        dt = datetime.fromtimestamp(v2)
        dt2 = datetime(dt.year, dt.month, dt.day, 0, 0)
        return int(dt2.strftime("%s"))

    def toString(self, val, local=True):
        val = self.clean(val)
        if val == 0:
            return ""
        return j.data.time.epoch2HRDate(val, local=local)


class Duration(String):
    """
    internal representation is an int (seconds)
    """

    NAME = "duration"

    def __init__(self, default=None):
        # inspired by https://stackoverflow.com/a/51916936
        self._RE = re.compile(
            r"^((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?((?P<minutes>[\.\d]+?)m)?((?P<seconds>[\.\d]+?)s)?$"
        )
        self.BASETYPE = "int"
        self.NOCHECK = True
        self._default = default

    def get_default(self):
        return 0

    def python_code_get(self, value):
        """
        produce the python code which represents this value
        """
        return self.clean(value)

    def check(self, value):
        """
        Check whether provided value is a valid duration representation
        be carefull is SLOW
        """
        try:
            self.clean(value)
            return True
        except:
            return False

    def fromString(self, txt):
        return self.clean(txt)

    def toString(self, val):
        val = self.clean(val)
        if val == 0:
            return ""
        days = val // 86400
        hours = (val - days * 86400) // 3600
        minutes = (val - days * 86400 - hours * 3600) // 60
        seconds = val - days * 86400 - hours * 3600 - minutes * 60
        return reduce(
            (lambda r, p: r + str(p[0]) + p[1] if p[0] > 0 else r),
            [(days, "d"), (hours, "h"), (minutes, "m"), (seconds, "s")],
            "",
        )

    def toHR(self, v):
        return self.toString(v)

    def clean(self, v):
        """
        support following formats:
        - None, 0: means undefined date
        - seconds = int
        - 1 (seconds)
        - 1s (seconds)
        - 2m (minutes)
        - 3h (hours)
        - 4d (days)
        - 1d4h2m3s (can also combine multiple, has to be from biggest to smallest and each unit has to be unique (e.g. cannot have 2 times hour specified))

        will return seconds
        """
        if v in [0, "0", None, ""]:
            return 0
        if j.data.types.string.check(v):
            v = v.replace("'", "").replace('"', "").strip()
            if v.isdigit():
                return int(v)  # shortcut for when string is an integer
            parts = self._RE.match(v)
            if parts is None:
                raise j.exceptions.Value(
                    "Could not parse any time information from '{}'.  Examples of valid strings: '8h', '2d8h5m20s', '2m4s'".format(
                        v
                    )
                )
            time_params = {name: float(param) for name, param in parts.groupdict().items() if param}
            return int(timedelta(**time_params).total_seconds())
        elif j.data.types.int.check(v):
            return v
        else:
            raise j.exceptions.Value("Input needs to be string or int: {} ({})".format(v, type(v)))

    def capnp_schema_get(self, name, nr):
        return "%s @%s :UInt32;" % (name, nr)
