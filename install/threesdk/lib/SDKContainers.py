from nacl.signing import SigningKey
from threesdk import english
import binascii
import requests

NETWORKS = {"mainnet": "explorer.grid.tf", "testnet": "explorer.testnet.grid.tf", "devnet": "explorer.devnet.grid.tf"}


class SDKContainers:
    def __init__(self, core, args):
        self.container = None
        self.image = "threefoldtech/3bot2"
        self.IT = core.IT
        self.core = core
        self.args = args

    def _get_user(self):
        resp = requests.get("https://{}/explorer/users".format(self.args.explorer), params={"name": self.args.identity})
        if resp.status_code == 404:
            return None
        else:
            users = resp.json()
            if users:
                return users[0]
            return None

    def _identity_ask(self, identity=None, explorer=None):
        def _fill_identity_args(identity, explorer):
            def fill_words():
                words = self.core.IT.Tools.ask_string("what are the words associated with your identity?")
                self.args.words = words

            if identity:
                if self.args.identity != identity:
                    self.args.reset()
                self.args.identity = identity

            if explorer:
                self.args.explorer = explorer
            elif not self.args.explorer:
                response = self.core.IT.Tools.ask_choices(
                    "Which network would you like to register to? ", ["mainnet", "testnet", "devnet", "none"]
                )
                self.args.explorer = NETWORKS.get(response, None)
            if not self.args.explorer:
                return True
            if not self.args.identity:
                identity = self.core.IT.Tools.ask_string("what is your threebot name (identity)?")
                if "." not in identity:
                    identity += ".3bot"
                self.args.identity = identity
            user = self._get_user()
            if not user and not self.args.email:
                email = self.core.IT.Tools.ask_string("what is your email associated with your identity?")
                self.args.email = email
            else:
                print("Configured email for this identity is {}".format(user["email"]))
                self.args.email = user["email"]
            if not self.args.words:
                if user:
                    fill_words()
                else:
                    self.args.words = None
            if user and self.args.words:
                # time to do validation of words
                while True:
                    try:
                        seed = self.core.IT.Tools.to_entropy(self.args.words, english.words)
                    except Exception:
                        choice = self.core.IT.Tools.ask_choices("Invalid words where given what would you like to do?", ["restart", "reenter"])
                        if choice == "restart":
                            return False
                        fill_words()
                        continue
                    # new we have a valid seed let's check if it matches the user
                    key = SigningKey(seed)
                    hexkey = binascii.hexlify(key.verify_key.encode()).decode()
                    if hexkey != user["pubkey"]:
                        choice = self.core.IT.Tools.ask_choices("Your words do not match your idenitiy, what would you like to do?", ["restart", "reenter"])
                        if choice == "restart":
                            return False
                        fill_words()
                        continue
                    return True

        while True:
            if _fill_identity_args(identity, explorer):
                return

    def _name(self, name):
        if name:
            if self.container and self.container.name != name:
                self.container = None
        else:
            if self.container:
                name = self.container.name
            else:
                name = "3bot"
                # self.IT.Tools.ask_string("name of the container (default 3bot):", default="3bot")
        return name

    def delete(self, name=None):
        name = self._name(name)
        self.IT.DockerFactory.container_delete(name=name)
        self.container = None

    def get(
        self,
        identity=None,
        name=None,
        delete=False,
        mount=True,
        email=None,
        words=None,
        secret=None,
        pull=False,
        code_update_force=False,
        explorer=None,
    ):
        """

        code_update_force: be careful, if set will remove your local code repo changes
        """
        name = self._name(name)
        self._identity_ask(identity, explorer)
        if not secret:
            secret = self.args.secret
        if not secret:
            self.args.secret = self.IT.Tools.ask_password("specify secret passphrase please:")
            secret = self.args.secret

        if self.container and not delete:
            return self.container

        # need to make sure 1 sshkey has been created, does not have to be in github
        if not self.IT.MyEnv.platform_is_windows:
            self.IT.MyEnv.sshagent.key_default_name

        self.IT.DockerFactory.init()

        docker = self.IT.DockerFactory.container_get(
            name=name, image=self.image, start=True, delete=delete, mount=mount, pull=pull
        )

        if not docker.executor.exists("/sandbox/cfg/.configured"):
            installer = self.IT.JumpscaleInstaller()
            print(" - make sure jumpscale code is on local filesystem.")
            installer.repos_get(pull=pull, branch=self.core.branch, reset=code_update_force)
            print(f" - install jumpscale for identity:{self.args.identity}")
            docker.install_jumpscale(
                force=False, reset=False, secret=self.args.secret, identity=self.args.identity, email=self.args.email, words=self.args.words, explorer=self.args.explorer
            )

            docker.executor.file_write("/sandbox/cfg/.configured", "")

        self.container = docker
        return docker
