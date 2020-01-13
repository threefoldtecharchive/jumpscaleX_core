from Jumpscale import j
from .SerializerBase import SerializerBase


class SerializerJSXObject(SerializerBase):
    def __init__(self):
        SerializerBase.__init__(self)

    def dumps(self, obj):
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
            + int(objid).to_bytes(4, "little")
            + bytes(bytearray.fromhex(obj._schema._md5))
            + data
        )

        # self._log_debug("DUMPS:%s:%s" % (version, obj.id), data=obj._ddict)

        return data2

    def loads(self, data, model=None, parent=None):
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
            schema_md5 = j.data.schema.get_from_md5(md5)
            schema = j.data.schema.get_from_url(schema_md5.url)
            assert schema_md5.url == schema.url
            # this will get us the newest version, not the one stored

            # MODEL SHOULD NEVER BE USED TO VALIDATE THE SCHEMA, ITS THE ROOT MODEL (not if subobj)

            obj = schema.new(capnpdata=data2, model=model, parent=parent)
            obj.id = obj_id
            if obj.id == 0:
                obj.id = None

            if model and model.schema.url == schema.url:
                # here the model retrieved will be linked to a schema with the same url
                model._triggers_call(obj=obj, action="new")
                # can only be done when a new root obj

            if md5 != schema._md5:
                if model and model.schema.url == schema.url:
                    model._triggers_call(obj, "schema_change", None)  # for the obj itself we need to force
                    model.schema_change(schema)
                    # don't add the obj, because need to do for all obj which are loaded

            return obj

        else:

            raise j.exceptions.Base("version wrong, versionnr found:%s (needs to be 1 or 10)" % versionnr)
