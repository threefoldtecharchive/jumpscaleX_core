from Jumpscale import j
import binascii
from Jumpscale.clients.threebot.ThreebotClient import ThreebotClient
from io import BytesIO
from nacl.signing import VerifyKey
from nacl.public import PrivateKey, PublicKey, SealedBox

JSConfigBase = j.baseclasses.object_config_collection


class ThreebotToolsFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.tools.threebot"
    _CHILDCLASS = ThreebotClient

    def _init(self):
        self._nacl = j.data.nacl.default

    @property
    def explorer(self):
        return j.clients.threebot.explorer

    def _serializer_get(self, serialization_format="json"):
        if not serialization_format in ["json", "msgpack"]:
            raise j.exceptions.Input("only support json or msgpack for serialize")
        if serialization_format == "json":
            return j.data.serializers.json
        if serialization_format == "msgpack":
            return j.data.serializers.msgpack

    def _unserialize_item(self, data, serialization_format="json"):
        """
        :param data: can be a binary blob or a list of items, which will be converted to binary counterpart
        :param serialization_format: json or msgpack

        unserialization as follows:

            int,float,str,binary,list and dict  -> stay in native format
            jsxobject -> jsxobject.json
            jsxdict -> jsxdict._data which is the source dict format of our jumpscale dict representation


        """
        serializer = self._serializer_get(serialization_format)

        if isinstance(data, str) or isinstance(data, int) or isinstance(data, float):
            return data
        elif isinstance(data, list) and len(data) == 2 and data[0] == 998:
            data2 = j.baseclasses.dict()
            data2._data = data[1]
            return data2
        elif isinstance(data, list) and len(data) == 3 and data[0] == 999:
            # means is jsxobject
            _, md5, json_str = data
            schema = j.data.schema.get_from_md5(md5)
            datadict = self._serializer_get(serialization_format="json").loads(json_str.encode())
            data = schema.new(datadict=datadict)
            return data
        elif isinstance(data, list) or isinstance(data, dict):
            return data
        else:
            try:
                return serializer.loads(data)
            except:
                return data

    def _serialize_item(self, data, serialization_format="json"):
        """
        :param data: can be a binary blob or a list of items, which will be converted to binary counterpart
        :param serialization_format: json or msgpack

        serialization as follows:

            int,float,str,binary,list and dict  -> stay in native format
            jsxobject -> jsxobject.json
            jsxdict -> jsxdict._data which is the source dict format of our jumpscale dict representation


        """
        serializer = self._serializer_get(serialization_format)

        if isinstance(data, str) or isinstance(data, int) or isinstance(data, float) or isinstance(data, bytes):
            return data
        if isinstance(data, j.data.schema._JSXObjectClass):
            return [999, data._schema._md5, data._json]
        if isinstance(data, j.baseclasses.dict):
            return [998, data._data]
        if isinstance(data, list) or isinstance(data, dict):
            return data
        raise j.exceptions.Input("did not find supported format")

    def serialize(self, data, serialization_format="json"):
        """
        :param data: a list which needs to be serialized, or single item
        :param serialization_format: json or msgpack

        members of the list (if a list) or the item itself if no list

            int,float,str,binary,list and dict  -> stay in native format
            jsxobject -> jsxobject.json
            jsxdict -> jsxdict._data which is the source dict format of our jumpscale dict representation


        return serialized list of serialized items
        or if no list
        return serialized item

        """
        serializer = self._serializer_get(serialization_format)
        if isinstance(data, list):
            res = []
            for item in data:
                res.append(self._serialize_item(item, serialization_format=serialization_format))
            return serializer.dumps(res)
        else:
            return serializer.dumps(data)

    def unserialize(self, data, serialization_format="json"):
        """
        :param data: a list which needs to be unserialized, or 1 item
        :param serialization_format: json or msgpack

        members of the list (if a list) or the item itself if no list

            int,float,str,binary,list and dict  -> stay in native format
            jsxobject -> jsxobject.json
            jsxdict -> jsxdict._data which is the source dict format of our jumpscale dict representation

        return unserialized list of unserialized items
        or if no list
        return serialized item

        """
        serializer = self._serializer_get(serialization_format)
        data = serializer.loads(data)
        if isinstance(data, list):
            res = []
            for item in data:
                res.append(self._unserialize_item(item, serialization_format=serialization_format))
            return res
        else:
            return self._unserialize_item(data, serialization_format=serialization_format)

    def serialize_sign_encrypt(self, data, serialization_format="json", pubkey_hex=None):
        """
        will sign any data with private key of our local 3bot private key
        if public_encryption_key given will then encrypt using the pub key given (as binary hex encoded key)

        :param data: can be a binary blob or a list of items, which will be converted to binary counterpart
        :param serialization_format: json or msgpack

        a list of following items

            int,float,str,binary,list and dict  -> stay in native format
            jsxobject -> jsxobject.json
            jsxdict -> jsxdict._data which is the source dict format of our jumpscale dict representation


        this gets serialized using the chosen format

        result is [3botid,serializeddata,signature]

        this then gets signed with private key of this threebot

        the serializeddata optionally gets encrypted with pubkey_hex (the person who asked for the info)

        :return: [3botid,serializeddata,signature]
        """
        data2 = self.serialize(data, serialization_format=serialization_format)
        tid = j.core.myenv.config["THREEBOT_ID"]
        if isinstance(data2, str):
            data2 = data2.encode()
        signature = self._nacl.sign(data2)
        if pubkey_hex:
            assert len(pubkey_hex) == 64
            pubkey = PublicKey(binascii.unhexlify(pubkey_hex))
            data3 = self._nacl.encrypt(data2, public_key=pubkey)
        else:
            data3 = data2
        return [tid, data3, signature]

    def deserialize_check_decrypt(self, data, serialization_format="json", verifykey_hex=None):
        """

        if pubkey_hex given will then check the signature (is binary encoded pub key)
        decryption will happen with the private key
        the serialization_format should be the one used in self.serialize_sign_encrypt()
        as we will use it to deserialize the encrypted data
        :param data: result of self.serialize_sign_encrypt()
        :param serialization_format: json or msgpack

        :return: [list of items] deserialized but which were serialized in data using serialization_format 
        raises exceptions if decryption or signature fails

        """

        # decrypt data
        data_dec_ser = self._nacl.decrypt(data[1])
        # unserialize data
        data_dec = self.unserialize(data_dec_ser, serialization_format=serialization_format)
        # verify the signature against the provided pubkey and the decrypted data
        sign_is_ok = self._nacl.verify(data_dec_ser, data[2], verify_key=binascii.unhexlify(verifykey_hex))
        if not sign_is_ok:
            raise j.exceptions.Base(
                "could not verify signature:%s, against pubkey:%s" % (data[2], binascii.unhexlify(verifykey_hex))
            )
        return data_dec

    def get_test_data(self):
        S = """
        @url = tools.threebot.test.schema
        name** = "aname"
        description = "something" 
        """
        schema = j.data.schema.get_from_text(S)
        jsxobject = schema.new()
        ddict = j.baseclasses.dict()
        ddict["a"] = 2
        data_list = [True, 1, [1, 2, "a"], jsxobject, "astring", ddict]
        return data_list

    def test(self, name=""):
        """
        following will run all tests

        kosmos 'j.tools.threebot.test()'
        :return:


        """

        print(name)
        if not "THREEBOT_ID" in j.core.myenv.config:
            j.core.myenv.config["THREEBOT_ID"] = 999999
        self._test_run(name=name)

        self._log_info("All TESTS DONE")
        return "OK"
