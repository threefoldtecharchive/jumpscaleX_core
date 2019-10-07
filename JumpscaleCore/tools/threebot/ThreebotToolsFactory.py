from Jumpscale import j
import binascii
from .ThreebotMe import ThreebotMe
from .ThreebotMeCollection import ThreebotMeCollection
from .ThreebotExplorer import ThreebotExplorer
from io import BytesIO
from nacl.signing import VerifyKey
from nacl.public import PrivateKey, PublicKey, SealedBox


class ThreebotToolsFactory(j.baseclasses.factory_testtools):
    __jslocation__ = "j.tools.threebot"
    _CHILDCLASSES = [ThreebotMeCollection]

    def _init(self):
        self._nacl = j.data.nacl.default
        self.explorer = ThreebotExplorer()

    def init_my_threebot(
        self, myidentity="default", name=None, email=None, description=None, ipaddr="", interactive=True
    ):
        """

        initialize your threebot

        kosmos 'j.tools.threebot.init_my_threebot(name="test2.ibiza",interactive=False)'

        :param myidentity is the name of the nacl to use, std default, is your private/public key pair

        :return:
        """
        j.application.interactive = interactive

        nacl = j.data.nacl.get(name=myidentity)
        assert nacl.verify_key_hex

        if not name:
            if interactive:
                name = j.tools.console.askString("your threebot name")
            else:
                raise j.exceptions.Input("please specify name")

        r = j.tools.threebot.explorer.threebot_record_get(name=name, die=False)
        if not r:
            # means record did not exist yet
            if not email:
                if interactive:
                    assert j.application.interactive
                    email = j.tools.console.askString("your threebot email (optional)")
                else:
                    email = ""
            if not description:
                if interactive:
                    description = j.tools.console.askString("your threebot description (optional)")
                else:
                    description = ""
            if not ipaddr:
                if str(j.core.platformtype.myplatform).startswith("darwin"):
                    ipaddr = "localhost"
                else:
                    ipaddr = j.sal.nettools.getIpAddress()["ip"][0]

            if interactive:
                if not j.tools.console.askYesNo("ok to use your local private key as basis for your threebot?", True):
                    raise j.exceptions.Input("cannot continue, need to register a threebot using j.clients.threebot")

            self.explorer.threebot_register(
                name=name, ipaddr=ipaddr, email=email, description=description, wallet_name=name, nacl=nacl
            )
            r = self.explorer.threebot_record_get(name=name, die=True)

        if not nacl.verify_key_hex == r.pubkey:
            raise j.exceptions.Input("your identity needs to be same pubkey as local configured nacl")

        assert r.id
        assert r.name

        o = self.me.get(name=myidentity, tid=r.id, tname=r.name, email=r.email, pubkey=r.pubkey)

        print(o)

        return o

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

    def _serialize(self, data, serialization_format="json"):
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

    def _unserialize(self, data, serialization_format="json"):
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

    def _serialize_sign_encrypt(self, data, serialization_format="json", pubkey_hex=None, nacl=None, threebot=None):
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
        if not nacl:
            nacl = self._nacl
        data2 = self._serialize(data, serialization_format=serialization_format)

        if isinstance(data2, str):
            data2 = data2.encode()
        signature = nacl.sign(data2)
        signature_hex = binascii.hexlify(signature)
        if threebot:
            threebot_client = j.clients.threebot.client_get(threebot)
            data3 = threebot_client.encrypt_for_threebot(data2)
            tid = threebot_client.tid
        else:
            tid = j.tools.threebot.me.default.tid
            if pubkey_hex:
                assert len(pubkey_hex) == 64
                pubkey = PublicKey(binascii.unhexlify(pubkey_hex))
                data3 = nacl.encrypt(data2, public_key=pubkey)
            else:
                data3 = data2
        return [tid, data3, signature_hex]

    def _deserialize_check_decrypt(
        self, data, serialization_format="json", verifykey_hex=None, nacl=None, threebot=None
    ):
        """

        if pubkey_hex given will then check the signature (is binary encoded pub key)
        decryption will happen with the private key
        the serialization_format should be the one used in self._serialize_sign_encrypt()
        as we will use it to deserialize the encrypted data
        :param data: result of self._serialize_sign_encrypt()
        :param serialization_format: json or msgpack

        :return: [list of items] deserialized but which were serialized in data using serialization_format 
        raises exceptions if decryption or signature fails

        """
        assert len(verifykey_hex) == 128
        if not nacl:
            nacl = self._nacl
        # decrypt data
        data_dec_ser = nacl.decrypt(data)
        # unserialize data
        data_dec = self._unserialize(data_dec_ser, serialization_format=serialization_format)
        # verify the signature against the provided pubkey and the decrypted data
        if threebot:
            threebot_client = j.clients.threebot.client_get(threebot)
            threebot_client.verify_from_threebot(data=data_dec_ser, signature=verifykey_hex)
        else:
            sign_is_ok = nacl.verify(data_dec_ser, data[2], verify_key=binascii.unhexlify(verifykey_hex))
            if not sign_is_ok:
                raise j.exceptions.Base(
                    "could not verify signature:%s, against pubkey:%s" % (data[2], binascii.unhexlify(verifykey_hex))
                )
        return data_dec

    def _get_test_data(self):
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

    def test_register_nacl_clients_get(self):
        """
        kosmos 'j.clients.threebot.test_register()'
        :return:
        """

        self.explorer.actors.package_manager.package_add(
            "threebot_phonebook",
            git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/phonebook",
        )

        j.servers.threebot.local_start_default()

        nacl1 = j.data.nacl.configure(name="test_client")
        nacl2 = j.data.nacl.configure(name="test_server")

        threebot1 = self.threebot_register(
            name="test.test", email="test@incubaid.com", ipaddr="212.3.247.26", nacl=nacl1
        )

        threebot2 = self.threebot_register(
            name="dummy.myself", email="dummy@incubaid.com", ipaddr="212.3.247.27", nacl=nacl2
        )

        return nacl1, nacl2, threebot1, threebot2

    def test_register_nacl_threebots(self):
        self.explorer.actors.package_manager.package_add(
            "threebot_phonebook",
            git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/phonebook",
        )

        # need to make sure to reload the client, because we added a package
        self.explorer._client.reload()

        nacl1 = j.data.nacl.get(name="test_client")
        nacl2 = j.data.nacl.get(name="test_server")

        # name needs to correspond with the nacl name, this is your pub/priv key pair
        threebot_me_client = j.tools.threebot.init_my_threebot(
            myidentity="test_client",
            name="test_client",
            email=None,
            description=None,
            ipaddr="localhost",
            interactive=False,
        )
        threebot_me_server = j.tools.threebot.init_my_threebot(
            myidentity="test_server",
            name="test_server",
            email=None,
            description=None,
            ipaddr="localhost",
            interactive=False,
        )

        return nacl1, nacl2, threebot_me_client, threebot_me_server

    def test(self, name=""):
        """

        this test needs the j.tools.threebot.me to exist (registration done)

        following will run all tests

        kosmos 'j.tools.threebot.test()'
        :return:


        """

        cl = j.servers.threebot.local_start_default()

        cl.actors.package_manager.package_add(
            "threebot_phonebook",
            git_url="https://github.com/threefoldtech/jumpscaleX_threebot/tree/master/ThreeBotPackages/threefold/phonebook",
        )

        self._threebot_client_default = cl

        self.me

        self._test_run(name=name)

        self._log_info("All TESTS DONE")
        return "OK"
