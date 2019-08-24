from Jumpscale import j
from .SerializerBase import SerializerBase


class SerializerJSXObject(SerializerBase):
    def __init__(self):
        SerializerBase.__init__(self)

    def dumps(self, obj, test=True):
        """
        obj is the dataobj for JSX

        j.data.serializers.jsxdata.dumps(..

        :param obj:
        :param test: if True will be slow !!!
        :return:
        """
        assert isinstance(obj, j.data.schema._JSXObjectClass)

        try:
            obj._capnp_obj.clear_write_flag()
            data = obj._capnp_obj.to_bytes_packed()
        except Exception as e:
            # need to catch exception much better (more narrow)
            obj._capnp_obj_ = obj._capnp_obj.as_builder()
            data = obj._capnp_obj_.to_bytes_packed()

        version = 3
        if obj.id:
            objid = obj.id
        else:
            objid = 0
        data2 = (
            version.to_bytes(1, "little")
            + objid.to_bytes(4, "little")
            + bytes(bytearray.fromhex(obj._schema._md5))
            + data
        )

        if test:
            u = self.loads(data=data2)
            assert u.id == obj.id

        # self._log_debug("DUMPS:%s:%s" % (version, obj.id), data=obj._ddict)

        return data2

    def loads(self, data, bcdb=None):
        """
        j.data.serializers.jsxdata.loads(..
        :param data:
        :return: obj
        """
        assert data

        versionnr = int.from_bytes(data[0:1], byteorder="little")

        if versionnr == 3:
            obj_id = int.from_bytes(data[1:5], byteorder="little")
            md5bin = data[5:21]
            md5 = md5bin.hex()
            data2 = data[21:]

            schema = j.data.schema.get_from_md5(md5)
            obj = schema.new(capnpdata=data2, bcdb=bcdb)
            obj.id = obj_id
            if obj.id == 0:
                obj.id = None
            return obj

        else:

            raise j.exceptions.Base("version wrong, versionnr found:%s (needs to be 1 or 10)" % versionnr)
