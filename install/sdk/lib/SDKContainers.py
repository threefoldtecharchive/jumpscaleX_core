class SDKContainers:
    def __init__(self, core, args):
        self.container = None
        self.image = "threefoldtech/3bot2"
        self.IT = core.IT
        self.core = core
        self.args = args

    def _identity_ask(self, identity=None):
        if not identity and self.args.identity:
            return self.args.identity
        if not identity:
            identity = self.core.IT.Tools.ask_string("what is your threebot name (identity)?")
        if "." not in identity:
            identity += ".3bot"
        identity = identity.lower()
        if self.args.identity != identity:
            self.args.identity = identity
            self.args.words = None
            self.args.email = None

        return identity

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
        docker = self.IT.DockerFactory.container_delete(name=name)
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
    ):
        """

        code_update_force: be careful, if set will remove your local code repo changes
        """
        name = self._name(name)

        identity = self._identity_ask(identity)

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

            if not identity.endswith(".test"):
                assert self.args.identity

            print(f" - install jumpscale for identity:{self.args.identity}")

            if not email:
                email = self.args.email
            if not words:
                words = self.args.words

            if not self.args.secret:
                self.args.secret = self.IT.Tools.ask_password("specify secret passphrase please:")

            if not secret:
                secret = self.args.secret

            docker.install_jumpscale(
                force=False, reset=False, secret=secret, identity=identity, email=email, words=words,
            )

            docker.executor.file_write(f"/sandbox/cfg/.configured", "")

        self.container = docker
        return docker
