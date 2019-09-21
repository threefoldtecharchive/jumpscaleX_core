from Jumpscale import j
import binascii
from .ThreebotMe import ThreebotMe
from io import BytesIO
from nacl.signing import VerifyKey
from nacl.public import PrivateKey, PublicKey, SealedBox

JSConfigBase = j.baseclasses.object_config_collection


class ThreebotToolsFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.tools.threebot"
    _CHILDCLASS = ThreebotMe

    def _init(self):
        self._nacl = j.data.nacl.default

    @property
    def me(self):
        """
        your default threebot data
        :return:
        """
        return self.get(name="default")

    def init(self, myidentity="default", name=None, email=None, description=None, ipaddr="", interactive=True):
        """

        kosmos 'j.tools.threebot.init(name="test2.ibiza",interactive=False)'

        :param myidentity is the name of the nacl to use, std default, is your private/public key pair

        initialize your threebot connection
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

        r = j.tools.threebot.threebot_record_get(name=name, die=False)
        if not r:
            # means record did not exist yet
            if not email:
                if interactive:
                    email = j.tools.console.askString("your threebot email (optional)")
                else:
                    email = ""
            if not description:
                if interactive:
                    description = j.tools.console.askString("your threebot description (optional)")
                else:
                    description = ""
            if not ipaddr:
                if interactive:
                    ipaddr = j.tools.console.askString("your threebot ipaddr (optional if used e.g. locally)")
                else:
                    ipaddr = ""

            if interactive:
                if not j.tools.console.askYesNo("ok to use your local private key as basis for your threebot?", True):
                    raise j.exceptions.Input("cannot continue, need to register a threebot using j.clients.threebot")

            j.clients.threebot.threebot_register(
                name=name, ipaddr=ipaddr, email=email, description=description, wallet_name=name, nacl=nacl
            )
            r = j.tools.threebot.threebot_record_get(name=name, die=True)

        if not nacl.verify_key_hex == r.pubkey:
            raise j.exceptions.Input("your identity needs to be same pubkey as local configured nacl")

        o = self.get(name=myidentity, tid=r.id, tname=r.name, email=r.email, pubkey=r.pubkey)

        return o

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
        tid = j.tools.threebot.me.tid
        if isinstance(data2, str):
            data2 = data2.encode()
        signature = nacl.sign(data2)
        if threebot:
            threebot_client = j.clients.threebot.get(threebot)
            data3 = threebot_client.encrypt_for_threebot(data2)
        else:
            if pubkey_hex:
                assert len(pubkey_hex) == 64
                pubkey = PublicKey(binascii.unhexlify(pubkey_hex))
                data3 = nacl.encrypt(data2, public_key=pubkey)
            else:
                data3 = data2
        return [tid, data3, signature]

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
        if not nacl:
            nacl = self._nacl
        # decrypt data
        data_dec_ser = nacl.decrypt(data[1])
        # unserialize data
        data_dec = self._unserialize(data_dec_ser, serialization_format=serialization_format)
        # verify the signature against the provided pubkey and the decrypted data
        if threebot:
            threebot_client = j.clients.threebot.get(threebot)
            threebot_client.verify_from_threebot(data=data_dec_ser, signature=verifykey_hex)
        else:
            sign_is_ok = nacl.verify(data_dec_ser, data[2], verify_key=binascii.unhexlify(verifykey_hex))
        if not sign_is_ok:
            raise j.exceptions.Base(
                "could not verify signature:%s, against pubkey:%s" % (data[2], binascii.unhexlify(verifykey_hex))
            )
        return data_dec

    def threebot_record_get(self, tid=None, name=None, die=True):
        """
        j.tools.threebot.threebot_record_get(name="something.something",die=False)
        :param tid: threebot id
        :param name: name of your threebot
        :param die:

        if data found will be verified on validity

        :return:
        """
        # did not find locally yet lets fetch
        r = self.explorer.client.actors.phonebook.get(tid=tid, name=name, die=die)
        if r and r.name != "":
            # this checks that the data we got is valid
            rc = j.data.nacl.payload_verify(
                r.id,
                r.name,
                r.email,
                r.ipaddr,
                r.description,
                r.pubkey,
                verifykey=r.pubkey,
                signature=r.signature,
                die=False,
            )
            if not rc:
                raise j.exceptions.Input("threebot record, not valid, signature does not match")

            return r

        if die:
            raise j.exceptions.Input("could not find 3bot: user_id:{user_id} name:{name}")

    def threebot_network_prepay_wallet(self, name):
        """

        the threebot will create a wallet for you as a user and you can leave money on there to be used for
        paying micro payment services on the threefold network (maximum amount is 1000 TFT on the wallet)
        THIS IS A WALLET MEANT FOR MICRO PAYMENTS ON THE NETWORK OF THE CORE NETWORK ITSELF !!!
        ITS AN ADVANCE ON SERVICES WHICH WILL BE USED E.G. REGISTER NAMES or NAME RECORDS

        if a wallet stays empty during 1 day it will be removed automatically

        :param: name is the name of the 3bot like how will be used in following functions like threebot_register_name
        :param: sender_signature_hex off the name as done by private key of the person who asks

        :return: a TFT wallet address
        """
        self._log_info("register step0: create your wallet under the name of your main threebot: %s" % name)
        cl = self.explorer_redis
        data_return_json = cl.execute_command(
            "default.phonebook.wallet_create", j.data.serializers.json.dumps({"name": name})
        )
        data_return = j.data.serializers.json.loads(data_return_json)
        return data_return["wallet_addr"]

    def threebot_register(self, name=None, ipaddr=None, email="", description="", wallet_name=None, nacl=None):
        """

        The cost is 20 TFT today to register a name which is valid for 1 Y.

        :param: name you want to register can eg $name.$extension of $name if no extension will be $name.3bot
                needs to correspond on the name as used in threebot_wallet_create
        :param: wallet_name is the name of a wallet you have funded, by default the same as your name you register
        :param email:
        :param ipaddr:
        :param description:
        :param nacl is the nacl instance you use default self.default which is for the local threebot
        :return:
        """
        assert name

        if not nacl:
            nacl = j.data.nacl.default
        pubkey = nacl.verify_key_hex

        self._log_info("register step1: for 3bot name: %s" % name)
        if not wallet_name:
            wallet_name = name
        cl = self.explorer_redis
        data_return_json = cl.execute_command(
            "default.phonebook.name_register",
            j.data.serializers.json.dumps({"name": name, "wallet_name": wallet_name, "pubkey": pubkey}),
        )

        data_return = j.data.serializers.json.loads(data_return_json)

        tid = data_return["id"]

        self._log_info("register: {id}:{name} {email} {ipaddr}".format(**data_return))

        # we choose to implement it low level using redis interface
        assert name
        assert tid
        assert isinstance(tid, int)

        data = {
            "tid": tid,
            "name": name,
            "email": email,
            "ipaddr": ipaddr,
            "description": description,
            "pubkey": pubkey,
        }

        def sign(nacl, *args):
            buffer = BytesIO()
            for item in args:
                if isinstance(item, str):
                    item = item.encode()
                elif isinstance(item, int):
                    item = str(item).encode()
                elif isinstance(item, bytes):
                    pass
                else:
                    raise RuntimeError()
                buffer.write(item)
            payload = buffer.getvalue()
            signature = nacl.sign(payload)
            return binascii.hexlify(signature).decode()

        # we sign the different records to come up with the right 'sender_signature_hex'
        sender_signature_hex = sign(
            nacl, data["tid"], data["name"], data["email"], data["ipaddr"], data["description"], data["pubkey"]
        )
        data["sender_signature_hex"] = sender_signature_hex
        data2 = j.data.serializers.json.dumps(data)
        data_return_json = cl.execute_command("default.phonebook.record_register", data2)
        data_return = j.data.serializers.json.loads(data_return_json)

        record0 = self.threebot_record_get(tid=data_return["id"])
        record1 = self.threebot_record_get(name=data_return["name"])

        assert record0 == record1

        self._log_info("registration of threebot '{%s}' done" % name)

        return record1

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

    def test_register_nacl_clients_get(self):
        """
        kosmos 'j.clients.threebot.test_register()'
        :return:
        """
        nacl1 = j.data.nacl.configure(name="client_test")
        nacl2 = j.data.nacl.configure(name="client_test2")

        threebot1 = self.threebot_register(
            name="test.test", email="test@incubaid.com", ipaddr="212.3.247.26", nacl=nacl1
        )

        threebot2 = self.threebot_register(
            name="dummy.myself", email="dummy@incubaid.com", ipaddr="212.3.247.27", nacl=nacl2
        )

        self._log_info("test ok")

        return nacl1, nacl2, threebot1, threebot2

    def test(self, name=""):
        """

        this test needs the j.tools.threebot.me to exist (registration done)

        following will run all tests

        kosmos 'j.tools.threebot.test()'
        :return:


        """

        self._test_run(name=name)

        self._log_info("All TESTS DONE")
        return "OK"
