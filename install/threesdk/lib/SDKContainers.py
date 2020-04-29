from nacl.signing import SigningKey
from threesdk import english
import binascii
import requests
import base64

NETWORKS = {"mainnet": "explorer.grid.tf", "testnet": "explorer.testnet.grid.tf", "devnet": "explorer.devnet.grid.tf"}


class SDKContainers:
    def __init__(self, core, args):
        self.container = None
        self.image = "threefoldtech/3bot2"
        self.IT = core.IT
        self.core = core
        self.args = args
        self._wireguard = None

    def _check_keys(self, hexkey):
        response = requests.get(f"https://login.threefold.me/api/users/{self.args.identity}")
        pub_key_app = base64.b64decode(response.json()["publicKey"])
        if binascii.unhexlify(hexkey) != pub_key_app:
            return False
        return True

    def _get_user(self):
        response = requests.get(f"https://login.threefold.me/api/users/{self.args.identity}")
        if response.status_code == 404:
            raise self.core.IT.Tools.exceptions.Value(
                "\nThis identity does not exist in 3bot mobile app connect, Please create an idenity first using 3Bot Connect mobile Application\n"
            )

        resp = requests.get("https://{}/explorer/users".format(self.args.explorer), params={"name": self.args.identity})
        if resp.status_code == 404:
            return None
        else:
            users = resp.json()
            pub_key_app = base64.b64decode(response.json()["publicKey"])
            pub_key_explorer = binascii.unhexlify(users[0]["pubkey"])

            if pub_key_app != pub_key_explorer:
                raise self.core.IT.Tools.exceptions.Value(
                    f"\nYour 3bot on {self.args.explorer} seems to have been previously registered with a different public key.\n"
                    "Please contact support.grid.tf to reset it.\n"
                    "Note: use the same email registered on the explorer to contact support otherwise we cannot reset the account.\n"
                )

            if users:
                return users[0]
            return None

    def _check_email(self, email):
        resp = requests.get("https://{}/explorer/users".format(self.args.explorer), params={"email": email})
        users = resp.json()
        if users:
            return True
        return False

    def _identity_ask(self, identity=None, explorer=None):
        def _fill_identity_args(identity, explorer):
            def fill_words():
                words = self.core.IT.Tools.ask_string("Copy the phrase from your 3bot Connect app here.")
                self.args.words = words

            if identity:
                if self.args.identity != identity and self.args.identity:
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
            if not user:
                while True:
                    if not self.args.email:
                        self.args.email = self.core.IT.Tools.ask_string(
                            "What is the email address associated with your identity?"
                        )
                    if not self._check_email(self.args.email):
                        break
                    else:
                        self.args.email = None
                        response = self.core.IT.Tools.ask_choices(
                            "This email is currently associated with another identity. What would you like to do?",
                            ["restart", "reenter"],
                        )
                        if response == "restart":
                            return False
            elif user:
                print("Configured email for this identity is {}".format(user["email"]))
                self.args.email = user["email"]

            if not self.args.words:
                fill_words()

            # time to do validation of words
            while True:
                try:
                    seed = self.core.IT.Tools.to_entropy(self.args.words, english.words)
                    key = SigningKey(seed)
                    hexkey = binascii.hexlify(key.verify_key.encode()).decode()

                    if (user and hexkey != user["pubkey"]) or not self._check_keys(hexkey):
                        raise Exception
                    else:
                        return True
                except Exception:
                    choice = self.core.IT.Tools.ask_choices(
                        "\nSeems one or more more words entered is invalid.\n" " What would you like to do?\n",
                        ["restart", "reenter"],
                    )
                    if choice == "restart":
                        return False
                    fill_words()
                    continue

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

    def assert_container(self, name):
        if not self.IT.DockerFactory.docker_assert() or not self.IT.DockerFactory.container_name_exists(name):
            raise self.IT.Tools.exceptions.NotFound(f"Please install container {name} first")

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
        if self.container and not delete:
            return self.container

        # if linux die will be false and docker will be installed during installation process
        if not self.IT.DockerFactory.docker_assert() or not self.IT.DockerFactory.container_name_exists(name):
            if explorer != "none":
                self._identity_ask(identity, explorer)
            if not secret:
                secret = self.args.secret
            if not secret:
                self.args.secret = self.args.ask_secret()
                secret = self.args.secret

        # need to make sure 1 sshkey has been created, does not have to be in github
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
                force=False,
                reset=False,
                secret=self.args.secret,
                identity=self.args.identity,
                email=self.args.email,
                words=self.args.words,
                explorer=self.args.explorer,
            )

            docker.executor.file_write("/sandbox/cfg/.configured", "")

        self.container = docker
        return docker

    @property
    def wireguard(self):
        if not self._wireguard:
            self._wireguard = self.IT.WireGuardServer(addr="127.0.0.1", port=self.config.sshport, myid=199)
        return self._wireguard
