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

            int,float,str,binary  -> stay in native format
            json.dumps(list)  -> list   
            json.dumps(dict) -> dict   
            jsxobject.json -> jsxobject  

        """
        serializer = self._serializer_get(serialization_format)

        if isinstance(data, str) or isinstance(data, int) or isinstance(data, float):
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

            int,float,str,binary  -> stay in native format
            list -> json.dumps(list)
            dict -> json.dumps(dict)
            jsxobject -> jsxobject.json

        """
        serializer = self._serializer_get(serialization_format)

        if isinstance(data, str) or isinstance(data, int) or isinstance(data, float) or isinstance(data, bytes):
            return data
        if isinstance(data, j.data.schema._JSXObjectClass):
            return data._json
        if isinstance(data, list):
            return serializer.dumps(data)
        if isinstance(data, dict):
            return serializer.dumps(data)
        if isinstance(data, j.baseclasses.dict):
            return serializer.dumps(data._data)
        raise j.exceptions.Input("did not find supported format")

    def serialize(self, data, serialization_format="json"):
        """
        :param data: a list which needs to be serialized, can be a list of 1 item ofcourse
        :param serialization_format: json or msgpack

        members of the list (if a list) or the item itself if no list

            int,float,str,binary  -> stay in native format
            list -> json.dumps(list)   (or other serialization format)
            dict -> json.dumps(dict)
            jsxobject -> jsxobject.json

        return serialized list of serialized items
        or if no list
        return serialized item

        """
        serializer = self._serializer_get(serialization_format)
        if not isinstance(data, list):
            raise j.exceptions.Input("only list supported")

        res = []
        for item in data:
            res.append(self._serialize_item(item, serialization_format=serialization_format))
        return serializer.dumps(res)

    def unserialize(self, data, serialization_format="json"):
        """
        :param data: a list which needs to be unserialized, can be a list of 1 item ofcourse
        :param serialization_format: json or msgpack

        members of the list (if a list) or the item itself if no list

            int,float,str,binary  -> stay in native format
            list -> json.dumps(list)   (or other serialization format)
            dict -> json.dumps(dict)
            jsxobject -> jsxobject.json

        return unserialized list of unserialized items
        or if no list
        return serialized item

        """
        serializer = self._serializer_get(serialization_format)
        data = serializer.loads(data)
        if not isinstance(data, list):
            raise j.exceptions.Input("only list supported")

        res = []
        for item in data:
            res.append(self._unserialize_item(item, serialization_format=serialization_format))
        return res

    def serialize_sign_encrypt(self, data, serialization_format="json", pubkey_hex=None):
        """
        will sign any data with private key of our local 3bot private key
        if public_encryption_key given will then encrypt using the pub key given (as binary hex encoded key)

        :param data: can be a binary blob or a list of items, which will be converted to binary counterpart
        :param serialization_format: json or msgpack

        a list of following items

            int,float,str,binary  -> stay in native format
            list -> json.dumps(list)
            dict -> json.dumps(dict)
            jsxobject -> jsxobject.json

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
            pubkey = PublicKey(binascii.unhexlify(pubkey_hex))
            data3 = self._nacl.encrypt(data2, public_key=pubkey)
        else:
            data3 = data2
        return [tid, data3, signature]

    def deserialize_check_decrypt(self, data, serialization_format="json", pubkey_hex=None):
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
        sign_is_ok = self._nacl.verify(data_dec_ser, data[2], verify_key=binascii.unhexlify(pubkey_hex))
        if not sign_is_ok:
            raise j.exceptions.Base(
                "could not verify signature:%s, against pubkey:%s" % (data[2], binascii.unhexlify(pubkey_hex))
            )
        return data_dec

    #
    # def _payload_check(self, id=None, name=None, email=None, ipaddr="", description="", pubkey_hex=None):
    #     assert name
    #     assert email
    #     assert id
    #
    #     if isinstance(pubkey_hex, bytes):
    #         pubkey_hex = pubkey_hex.decode()
    #     assert isinstance(pubkey_hex, str)
    #     assert len(pubkey_hex) == 64
    #
    #     pubkey = binascii.unhexlify(pubkey_hex)
    #
    #     n = j.data.nacl.default
    #
    #     buffer = BytesIO()
    #     buffer.write(str(id).encode())
    #     buffer.write(name.encode())
    #     buffer.write(email.encode())
    #     buffer.write(ipaddr.encode())
    #     buffer.write(description.encode())
    #     buffer.write(pubkey_hex.encode())
    #
    #     # payload = name + email + pubkey + ipaddr + description
    #     payload = buffer.getvalue()
    #     signature = n.sign(payload)
    #
    #     signature_hex = binascii.hexlify(signature).decode()
    #
    #     # need to show how to use the pubkey to verify the signature & get the data
    #     assert n.verify(payload, signature, verify_key=pubkey)
    #
    #     return signature_hex
    def get_test_data(self):
        dico = {}
        dico["a"] = 1
        dico["yolo"] = "yeeh"
        data_list = [42, 5.6, "lorem ipsum gloria dea alea jacta es", dico, ["uouo", dico]]
        return data_list

    def test(self, name=""):
        """
        following will run all tests

        kosmos 'j.tools.threebot.test()'
        :return:


        """

        print(name)
        if not "THREEBOT_ID" in j.core.myenv.config:
            j.core.myenv.config["THREEBOT_ID"] = "t1000.advanced.prototype"
        self._test_run(name=name)

        self._log_info("All TESTS DONE")
        return "OK"
