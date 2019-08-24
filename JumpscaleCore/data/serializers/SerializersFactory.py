from Jumpscale import j


class SerializersFactory(j.baseclasses.object):

    __jslocation__ = "j.data.serializers"
    _msgpack = None
    _base64 = None
    _json = None
    _crc = None
    _int = None
    _yaml = None
    _base = None
    _lzma = None
    _pickle = None
    _blowfish = None
    _dict = None
    _blosc = None
    _snappy = None
    _dumper = None
    _toml = None
    _jsxdata = None

    @property
    def jsxdata(self):
        if self.__class__._jsxdata is None:
            from .SerializerJSXObject import SerializerJSXObject

            self.__class__._jsxdata = SerializerJSXObject()
        return self.__class__._jsxdata

    @property
    def yaml(self):
        if self.__class__._yaml is None:
            from .SerializerYAML import SerializerYAML

            self.__class__._yaml = SerializerYAML()
        return self.__class__._yaml

    @property
    def int(self):
        if self.__class__._int is None:
            from .SerializerInt import SerializerInt

            self.__class__._int = SerializerInt()
        return self.__class__._int

    @property
    def crc(self):
        if self.__class__._crc is None:
            from .SerializerCRC import SerializerCRC

            self.__class__._crc = SerializerCRC()
        return self.__class__._crc

    @property
    def base(self):
        if self.__class__._base is None:
            from .SerializerBase import SerializerBase

            self.__class__._base = SerializerBase()
        return self.__class__._base

    @property
    def toml(self):
        if self.__class__._toml is None:
            from .SerializerTOML import SerializerTOML

            self.__class__._toml = SerializerTOML()
        return self.__class__._toml

    @property
    def lzma(self):
        if self.__class__._lzma is None:
            from .SerializerLZMA import SerializerLZMA

            self.__class__._lzma = SerializerLZMA()
        return self.__class__._lzma

    @property
    def base64(self):
        if self.__class__._base64 is None:
            from .SerializerBase64 import SerializerBase64

            self.__class__._base64 = SerializerBase64()
        return self.__class__._base64

    @property
    def json(self):
        if self.__class__._json is None:
            from .SerializerUJson import SerializerUJson

            self.__class__._json = SerializerUJson()
        return self.__class__._json

    @property
    def pickle(self):
        if self.__class__._pickle is None:
            from .SerializerPickle import SerializerPickle

            self.__class__._pickle = SerializerPickle()
        return self.__class__._pickle

    @property
    def blowfish(self):
        if self.__class__._blowfish is None:
            from .SerializerBlowfish import SerializerBlowfish

            self.__class__._blowfish = SerializerBlowfish()
        return self.__class__._blowfish

    @property
    def dict(self):
        if self.__class__._dict is None:
            from .SerializerDict import SerializerDict

            self.__class__._dict = SerializerDict()
        return self.__class__._dict

    @property
    def blosc(self):
        if self.__class__._blosc is None:
            from .SerializerBlosc import SerializerBlosc

            self.__class__._blosc = SerializerBlosc()
        return self.__class__._blosc

    @property
    def msgpack(self):
        if self.__class__._msgpack is None:
            from .SerializerMSGPack import SerializerMSGPack

            self.__class__._msgpack = SerializerMSGPack()
        return self.__class__._msgpack

    @property
    def snappy(self):
        if self.__class__._snappy is None:
            from .SerializerSnappy import SerializerSnappy

            self.__class__._snappy = SerializerSnappy()
        return self.__class__._snappy

    @property
    def dumper(self):
        if self.__class__._dumper is None:
            from .PrettyYAMLDumper import PrettyYAMLDumper

            self.__class__._dumper = PrettyYAMLDumper()
        return self.__class__._dumper
