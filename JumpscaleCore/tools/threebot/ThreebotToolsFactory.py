from Jumpscale import j
import binascii
from .ThreebotClient import ThreebotClient
from io import BytesIO
from nacl.signing import VerifyKey

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
        signature = self._nacl.signing_key.sign(data2)
        if pubkey_hex:
            pubkey = binascii.unhexlify(pubkey_hex)
            data3 = ""  # TODO: encrypt using pubkey
        else:
            data3 = data2
        return [tid, data3, signature]

    def deserialize_check_decrypt(self, data, serialization_format="json", pubkey_hex=None):
        """

        if public_encryption_key given will then check the signature (is binary encoded pub key)
        decryption will happen with the private key

        :param data: result of self.serialize_sign_encrypt()
        :param serialization_format: json or msgpack

        :return: [list of items] which were serialized using self.serialize()

        """
        # TODO:
        pass

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

    def test(self):
        """
        kosmos 'j.tools.threebot.test()'
        :return:
        """

        # simulate I am remote threebot
        client_nacl = ""  # TODO create a new nacl
        server_nacl = j.data.nacl.default (the one we have)

        server_tid = j.core.myenv.config["THREEBOT_ID"]
        client_tid = 99

        self._nacl = client_nacl
        data = [True, 1, [1, 2, "a"], jsxobject, "astring"]
        data_send_over_wire = self.serialize_sign_encrypt(
            data, pubkey_hex=server_nacl.pubkey
        )  # todo select right pubkey

        # client send the above to server

        #now we are server
        self._nacl = server_nacl

        # server just returns the info

        data_readable_on_server = self.deserialize_check_decrypt(data_send_over_wire, pubkey_hex=client_nacl.pubkey)
        # data has now been verified with pubkey of client

        assert data_readable_on_server == [True, 1, [1, 2, "a"], jsxobject._json, "astring"]

        # lets now return the data to the client

        data_send_over_wire_return = self.serialize_sign_encrypt(data, pubkey_hex=client_nacl.pubkey)

        #now we are client
        self._nacl = client_nacl
        # now on client we check
        data_readable_on_client = self.deserialize_check_decrypt(
            data_send_over_wire_return, pubkey_hex=server_nacl.pubkey
        )

        #back to normal
        self._nacl = server_nacl
        j.core.myenv.config["THREEBOT_ID"] = server_tid



        self._log_info("test ok")
