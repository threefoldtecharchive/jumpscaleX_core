from .MeEncryptor import MeEncryptor
from Jumpscale import j

JSConfigBase = j.baseclasses.object_config


class Me(JSConfigBase):
    """
    represents me
    """

    _SCHEMATEXT = """
    @url = jumpscale.threebot.me
    name** = ""
    tid =  0 (I)                    #my threebot id
    tname = "me" (S)                #my threebot name
    email = "" (S)
    privkey = ""
    pubkey = ""                     
    admins = (LS)                   #3bot names which are admin of this 3bot (corresponds to 3bot connect name)
    sshkey_name = ""
    sshkey_pub = ""
    sshkey_priv = ""
    secret_expiration_hours = 48 (I)
    """

    def _init(self, **kwargs):
        # the threebot config name always corresponds with the config name of nacl, is by design
        self._encryptor = None
        self._secret = None

        self.serialization_format = "json"
        if not self.name:
            raise j.exceptions.Input(
                "threebot.me not filled in, please do j.tools.threebot.init_my_threebot(interactive=True)"
            )
        self._model.trigger_add(self._update_data)

    def secret_set(self, secret=None):
        """
        can be the hash or the originating secret passphrase
        """
        if not secret:
            secret = j.tools.console.askString("please specify secret (<32chars)")
            assert len(secret) < 32
        if len(secret) != 32:
            secret = j.data.hash.md5_string(secret)
        expiration = self.secret_expiration_hours * 3600
        j.core.db.set("threebot.secret.encrypted", secret, ex=expiration)

    @property
    def secret(self):
        if not self._secret:
            self._secret = j.core.db.get("threebot.secret.encrypted")
            if not self._secret:
                if j.application.interactive:
                    self.secret_set()
                else:
                    raise j.exceptions.Input("secret passphrase not known, need to set it for identity:%s" % self.name)
        return self._secret

    def _update_data(self, model, obj, action, propertyname):
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
        if action == "set_post":
            j.shell()

    @property
    def encryptor(self):
        if not self._encryptor:
            self._encryptor = MeEncryptor(me=self)
        return self._encryptor

    def configure_privatekey(self, words=None, reset=False, generate=False):
        """
        @param generate: generate now one,
        """
        if generate:
            reset = True

        key = None

        if reset:
            self.privkey = ""
            self.pubkey = ""

        if words:
            j.shell()

        if not self.privkey or not self.pubkey:
            generate = True

        if generate:
            if j.application.interactive:
                self.privkey = self.encryptor.words_ask()
            else:
                self.privkey = self.encryptor._priv_key_generate()

        self.pubkey = self.encryptor.public_key_hex

    def configure_sshkey(self, name=None, reset=False, generate=False):
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
                    "Will generate a ssh key, please specify name of your key, default='default'"
                )
            key = j.clients.sshkey.get(name=name)
            key.generate(reset=True)
            return key

        if generate:
            key = generate_ssh(name)

        if self.sshkey_priv and self.sshkey_pub and self.sshkey_name:
            if j.tools.console.askYesNo(f"ok to use ssh key: {self.sshkey_name}"):
                return

        keys = j.clients.sshkey.find()
        if not key and len(keys) == 1:
            key = keys[0]
            if not j.tools.console.askYesNo(f"found preconfigured key, ok to use ssh key: {key.name}"):
                key = None

        if not key and j.clients.sshagent.available and len(j.clients.sshagent.key_names) > 0:
            key = j.clients.sshagent.key_default
            if not j.tools.console.askYesNo(f"found key in sshagent, ok to use ssh key: {key.name}"):
                key = None

        if not key and len(keys) > 1:
            names = [key.name for key in keys]
            names.append("NEW")
            c = j.tools.console.askChoice(
                names,
                descr="Found multiple preconfigered keys, want to use one of those? If yes specify otherwise select NEW.",
            )
            if c != "NEW":
                key = j.clients.sshkey.get(c)

        if not key and j.tools.console.askYesNo("Cannot find a ssh key, ok to generate a new one?"):
            key = generate_ssh(name)

        self.sshkey_name = key.name
        self.sshkey_priv = key.privkey
        self.sshkey_pub = key.pubkey

    def configure(self):
        intro = True

        def dointro(intro):
            if intro:
                j.tools.console.clear_screen()
                print("THREEBOT IDENTITY NOT PROVIDED YET, WILL ASK SOME QUESTIONS NOW\n\n")
            return False

        while not self.tname:
            intro = dointro(intro)
            self.tname = j.tools.console.askString("please provide your threebot connect name")
        while not self.email:
            intro = dointro(intro)
            self.email = j.tools.console.askString("please provide your email")
            if "@" not in self.email:
                print("please specify valid email")
                self.email = ""
                print()
        while not self.sshkey_priv or not self.sshkey_pub or not self.sshkey_name:
            intro = dointro(intro)
            j.debug()
            self.configure_sshkey()

        self.save()

    # def sign(self, data):
    #     raise
    #     # TODO: implement
    #
    # def data_send_serialize(self, threebot, data):
    #     """
    #     data to send to a threebot needs to be encrypted with pub key of the threebot
    #     the data is unencrypted (a list of values or the value), default serialization = json
    #     :param threebot:
    #     :param data:
    #     :return:
    #     """
    #     return j.tools.threebot._serialize_sign_encrypt(
    #         data=data, serialization_format=self.serialization_format, threebot=threebot, nacl=self.nacl
    #     )
    #
    # def data_received_unserialize(self, threebot, data, signature):
    #     """
    #     data which came from a threebot needs to be unserialized and verified
    #     the data comes in encrypted
    #     :param threebot:
    #     :param data:
    #     :param signature: is the verification key in hex
    #     :return:
    #     """
    #     return j.tools.threebot._deserialize_check_decrypt(
    #         data=data,
    #         serialization_format=self.serialization_format,
    #         threebot=threebot,
    #         verifykey_hex=signature,
    #         nacl=self.nacl,
    #     )

    # def sign(self, data):
    #     raise
    #     # TODO: implement
    #
    # def data_send_serialize(self, threebot, data):
    #     """
    #     data to send to a threebot needs to be encrypted with pub key of the threebot
    #     the data is unencrypted (a list of values or the value), default serialization = json
    #     :param threebot:
    #     :param data:
    #     :return:
    #     """
    #     return j.tools.threebot._serialize_sign_encrypt(
    #         data=data, serialization_format=self.serialization_format, threebot=threebot, nacl=self.nacl
    #     )
    #
    # def data_received_unserialize(self, threebot, data, signature):
    #     """
    #     data which came from a threebot needs to be unserialized and verified
    #     the data comes in encrypted
    #     :param threebot:
    #     :param data:
    #     :param signature: is the verification key in hex
    #     :return:
    #     """
    #     return j.tools.threebot._deserialize_check_decrypt(
    #         data=data,
    #         serialization_format=self.serialization_format,
    #         threebot=threebot,
    #         verifykey_hex=signature,
    #         nacl=self.nacl,
    #     )

    def backup(self, stop=True):
        """
        kosmos 'j.tools.threebot.backup_local(stop=True)'
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
