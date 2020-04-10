from .MeEncryptor import MeEncryptor
from Jumpscale import j
import binascii

JSConfigBase = j.baseclasses.object_config


class Me(JSConfigBase, j.baseclasses.testtools):
    """
    represents me
    """

    _SCHEMATEXT = """
    @url = jumpscale.threebot.me
    name** = ""
    tid =  0 (I)                  #my threebot id
    tname = "" (S)                #my threebot name
    email = "" (S)
    signing_key = ""
    verify_key = ""
    admins = (LS)                   #3bot names which are admin of this 3bot (corresponds to 3bot connect name)
    sshkey_name = ""
    sshkey_pub = ""
    sshkey_priv = ""
    """

    def _init(self, **kwargs):
        # the threebot config name always corresponds with the config name of nacl, is by design
        self._encryptor = None

        self.serialization_format = "json"
        if not self.name:
            raise j.exceptions.Input(
                "threebot.me not filled in, please configure your identity"
            )
        self._model.trigger_add(self._update_data)

    def load(self):
        """
        kosmos 'j.me.configure(tname="my3bot")'
        """
        if self.tname and len(self.tname) > 4:
            path = j.core.tools.text_replace("{DIR_BASE}/myhost/identities/%s.toml" % self.tname)
            if j.sal.fs.exists(path):
                text_toml = j.sal.fs.readFile(path)
                self._data._data_update(j.data.serializers.toml.loads(text_toml))
                return
        path = j.core.tools.text_replace("{DIR_BASE}/myhost/identities/default")
        if j.sal.fs.exists(path):
            self.tname = j.core.tools.file_read(path).strip()
            return self.load()

    def reset(self):
        self.delete()

    def _update_data(self, model, obj, action, propertyname):
        if action == "delete":
            return
        if propertyname == "admins" or action == "set_pre":
            # make sure we have 3bot at end if not specified
            if len(self.tname) < 5:
                raise j.exceptions.Input("threebot name needs to be 5 or more letters.")
            if "." not in self.tname:
                self.tname += ".3bot"

        if propertyname == "admins" or action == "set_pre":
            # make sure we have 3bot at end if not specified
            r = []
            change = False
            for admin in self.admins:

                if admin.strip() == "":
                    change = True
                    continue
                if len(admin) < 5:
                    raise j.exceptions.Input("admin needs to be 5 or more letters.")
                if "." not in admin:
                    change = True
                    admin += ".3bot"
                r.append(admin)
            if change:
                self.admins = r

            # you are always yourself an admin, lets add
            if self.tname not in self.admins:
                self.admins.append(self.tname)

        if action == "set_post":
            # now write to local identity drive
            print(" - save identity:%s" % self.tname)
            j.sal.fs.createDir("{DIR_BASE}/myhost/identities")

            spath = "{DIR_BASE}/myhost/identities/%s.toml" % self.tname
            j.sal.fs.writeFile(spath, self._data._toml)

            defaultpath = "{DIR_BASE}/myhost/identities/default"
            if not j.sal.fs.exists(defaultpath):
                j.sal.fs.writeFile(defaultpath, self.tname)

    @property
    def encryptor(self):
        if not self._encryptor:
            self._encryptor = MeEncryptor(me=self)
        return self._encryptor

    def configure_encryption(self, words=None, reset=False, generate=False):
        """
        @param generate: generate now one,
        """
        j.tools.console.clear_screen()
        print(" *** WILL NOW CONFIGURE YOUR PRIVATE 3BOT SECURE KEY (IMPORTANT) ***\n\n")

        if generate:
            reset = True

        key = None

        if reset:
            self.signing_key = ""
            self.verify_key = ""

        if words:
            j.shell()

        if not self.signing_key or not self.verify_key:
            generate = True

        if generate:
            if j.application.interactive:
                self.signing_key = self.encryptor.words_ask()
            else:
                self.signing_key = self.encryptor._signing_key_generate()

        self.verify_key = self.encryptor.verify_key_hex

        j.tools.console.clear_screen()

    def configure_sshkey(self, name=None, reset=False, generate=False):
        j.tools.console.clear_screen()
        print(" *** WILL NOW CONFIGURE SSH KEY FOR USE IN 3BOT ***\n\n")
        if generate:
            reset = True
            if not name:
                name = self.name

        key = None

        if reset:
            self.sshkey_priv = ""
            self.sshkey_pub = ""
            self.sshkey_name = ""

        def generate_ssh(name):
            if not name:
                name = j.tools.console.askString(
                    "SSH: Will generate a ssh key, please specify name of your key, default='default'"
                )
            key = j.clients.sshkey.get(name=name)
            key.generate(reset=True)
            return key

        if generate:
            key = generate_ssh(name)

        if self.sshkey_priv and self.sshkey_pub and self.sshkey_name:
            if j.tools.console.askYesNo(f"SSH: ok to use ssh key: {self.sshkey_name}"):
                return

        keys = j.clients.sshkey.find()
        if not key and len(keys) == 1:
            key = keys[0]
            if not j.tools.console.askYesNo(f"SSH: found preconfigured SSH key, ok to use ssh key: {key.name}"):
                key = None

        if not key and j.clients.sshagent.available and len(j.clients.sshagent.key_names) > 0:
            key = j.clients.sshagent.key_default
            if not j.tools.console.askYesNo(f"SSH: found key in sshagent, ok to use ssh key: {key.name}"):
                key = None

        if not key and len(keys) > 1:
            names = [key.name for key in keys]
            names.append("NEW")
            c = j.tools.console.askChoice(
                names,
                descr="SSH: Found multiple preconfigered keys, want to use one of those? If yes specify otherwise select NEW.",
            )
            if c != "NEW":
                key = j.clients.sshkey.get(c)

        if not key and j.tools.console.askYesNo("SSH: Cannot find a ssh key, ok to generate a new one?"):
            key = generate_ssh(name)

        self.sshkey_name = key.name
        self.sshkey_priv = key.privkey
        self.sshkey_pub = key.pubkey

        j.tools.console.clear_screen()

    def configure(self, tname=None, ask=True, reset=False):

        """
        kosmos 'j.me.configure()'
        kosmos 'j.me.configure(tname="my3bot",ask=False)'
        kosmos 'j.me.configure(tname="my3bot",reset=True)'

        """

        if tname:
            self.tname = tname

        if reset:
            self.reset()

        intro = True

        def dointro(intro):
            if intro:
                j.tools.console.clear_screen()
                print("THREEBOT IDENTITY NOT PROVIDED YET, WILL ASK SOME QUESTIONS NOW\n\n")
            return False

        ask1 = bool(ask)
        while ask1 or not self.tname or len(self.tname) < 5:
            intro = dointro(intro)
            self.tname = j.tools.console.askString(
                "please provide your threebot connect name (min 5 chars)", default=self.tname
            )
            ask1 = False

        if not self.signing_key and len(self.tname) > 4:
            self.load()

        ask1 = bool(ask)
        while ask1 or not self.email or len(self.email) < 6 or "@" not in self.email:
            intro = dointro(intro)
            self.email = j.tools.console.askString("please provide your email", default=self.email)
            if "@" not in self.email:
                print("please specify valid email")
                self.email = ""
                print()
            ask1 = False

        while not self.sshkey_priv or not self.sshkey_pub or not self.sshkey_name:
            intro = dointro(intro)
            self.configure_sshkey()
        while not self.verify_key or not self.signing_key:
            self.configure_encryption(generate=True)

        if ask and j.tools.console.askYesNo("want to add threebot administrators?"):
            admins = ""
            if len(self.admins) > 0:
                admins = ",".join(self.admins)
            admins = j.tools.console.askString("please provide admins (comma separated)", default=admins)
            r = []
            for admin in admins.split(","):
                if admin.strip() == "":
                    continue
                if not admin in r:
                    r.append(admin)
            self.admins = admins

        self.save()

    def sign(self, data):
        return self.encryptor.sign(data)

    def data_send_serialize(self, threebot, data, serialization_format="json"):
        """
        data to send to a threebot needs to be encrypted with pub key of the threebot
        the data is unencrypted (a list of values or the value), default serialization = json
        :param threebot:
        :param data:
        :return:
        """
        return self.encryptor.tools._serialize_sign_encrypt(data, serialization_format, threebot=threebot)

    def data_received_unserialize(self, threebot, data, signature, serialization_format="json"):
        """
        instead of deprecated j.me._deserialize_check_decrypt

        data which came from a threebot needs to be unserialized and verified
        the data comes in encrypted
        :param threebot:
        :param data:
        :param signature: is the verification key in hex
        :return:
        """
        return self._deserialize_check_decrypt(data, serialization_format, signature, threebot)

    def backup(self, stop=True):
        """
        kosmos 'j.me.backup(stop=True)'
        :return:
        """
        if stop:
            j.servers.threebot.default.stop()
            j.data.bcdb._master_set()

        j.data.bcdb.start_servers_threebot_zdb_sonic()
        j.data.bcdb.export()

        if stop:
            j.servers.threebot.default.stop()

        j.tools.restic.delete(name="explorer_backup")
        b = j.tools.restic.get(name="explorer_backup")
        b.secret_ = j.core.myenv.adminsecret
        b.sources = []
        s = b.sources.new()
        s.paths.append("/sandbox/cfg")
        s.paths.append("/sandbox/var/bcdb")
        s.paths.append("/sandbox/var/bcdb_exports")
        s.paths.append("/sandbox/var/zdb")
        s.paths.append("/sandbox/code")
        b.dest.backupdir = "/root/backups"
        b.backup()

    # def backup_remote(self):
    #     cl = j.clients.ssh.get(name="explorer")
    #     raise RuntimeError("need to implement")

    def tfgrid_phonebook_register(self, host="", interactive=True):
        """

        initialize your threebot

        kosmos 'j.me.tfgrid_phonebook_register'

        :return:
        """
        # print("TODO USE DATA ON THIS OBJECT")
        # j.shell()
        j.application.interactive = interactive
        explorer = j.clients.explorer.default
        nacl = self.encryptor
        assert nacl.verify_key_hex
        try:
            r = explorer.users.get(name=self.tname)
        except j.exceptions.NotFound:
            r = None

        if not r:
            if interactive:
                description = j.tools.console.askString("your threebot description (optional)")
            else:
                description = ""

            if not host:
                if str(j.core.platformtype.myplatform).startswith("darwin"):
                    host = "localhost"
                else:
                    try:
                        (iface, host) = j.sal.nettools.getDefaultIPConfig()
                    except:
                        host = "localhost"

            if interactive:
                if not j.tools.console.askYesNo("ok to use your local private key as basis for your threebot?", True):
                    raise j.exceptions.Input("cannot continue, need to register a threebot using j.clients.threebot")

            user = explorer.users.new()
            user.name = self.name
            user.host = host
            user.email = self.email
            user.description = description
            user.pubkey = nacl.verify_key_hex
            tid = explorer.users.register(user)
            r = explorer.users.get(tid=tid)

        # why didn't we use the primitives as put on this factory (sign, decrypt, ...)
        # this means we don't take multiple identities into consideration, defeates the full point of our identity manager here
        payload = nacl.payload_build(r.id, r.name, r.email, r.host, r.description, nacl.verify_key_hex)
        payload = j.data.hash.bin2hex(payload).decode()
        signature = nacl.payload_sign(r.id, r.name, r.email, r.host, r.description, nacl.verify_key_hex, nacl=nacl)
        valid = explorer.users.validate(r.id, payload, signature)
        if not valid:
            raise j.exceptions.Input(
                "signature verification failed, ensure your pubkey to be the same as local configured nacl "
            )

        if not nacl.verify_key_hex == r.pubkey:
            raise j.exceptions.Input("your identity needs to be same pubkey as local configured nacl")

        assert r.id
        assert r.name
        self.tid = r.id
        self.save()

        print(self)

        return self

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

    def test(self, name=""):
        """

        this test needs the j.me to exist (registration done)

        following will run all tests

        kosmos 'j.me.test()'
        :return:



        """

        self._tests_run(name=name, die=True)

        self._log_info("All TESTS DONE")
        return "OK"
