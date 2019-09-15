import os
from Jumpscale import j

JSConfigClient = j.baseclasses.object_config


class RsyncServer(JSConfigClient):
    _SCHEMATEXT = """
           @url =  jumpscale.servers.rsync.1
           name** = "default" (S)
           root =  (S)
           port = 873 (I)
           dir = "" (S)
           """

    def _init(self, **kwargs):
        if not self.root:
            raise j.exceptions.Input("root can't be empty")

        self._startupcmd = None

        self.path_secrets = j.tools.path.get("%s/secrets.cfg" % self.root)
        self.path_users = j.tools.path.get("%s/users.cfg" % self.root)
        if self.dir == "":
            self.dir = "%s/apps/agentcontroller/distrdir/" % j.dirs.BASEDIR

        self.distrdir = j.tools.path.get(self.dir)
        if not self.distrdir.exists():
            j.sal.fs.createDir(self.dir)

        self.rolesdir = j.tools.path.get(self.root).joinpath("roles")

        j.tools.path.get("/etc/rsync").mkdir_p()

        if self.path_secrets.exists():
            self.secrets = j.data.serializers.toml.loads(self.path_secrets.text())
        else:
            self.secrets = {}

        if self.path_users.exists():
            self.users = j.data.serializers.toml.loads(self.path_users.text())
        else:
            self.users = {}

    def secret_add(self, name, secret=""):
        if name in self.secrets and secret == "":
            # generate secret
            secret = self.secrets[name]
        if secret == "":
            secret = j.data.idgenerator.generateGUID().replace("-", "")

        self.secrets[name.strip()] = secret.strip()
        self.path_secrets.write_text(j.data.serializers.toml.dumps(self.secrets))

    def user_add(self, name, passwd):
        self.users[name.strip()] = passwd.strip()
        self.path_users.write_text(j.data.serializers.toml.dumps(self.users))

    def config_save(self):

        C = """
        #motd file = /etc/rsync/rsyncd.motd
        port = $port
        log file=/var/log/rsync
        max verbosity = 1

        [upload]
        exclude = *.pyc .git
        path = $root/root
        comment = upload
        uid = root
        gid = root
        read only = false
        auth users = $users
        secrets file = /etc/rsync/users

        """
        D = """
        [$secret]
        exclude = *.pyc .git
        path = $root/root/$name
        comment = readonlypart
        uid = root
        gid = root
        read only = true
        list = no

        """
        C = j.core.text.strip(C)
        users = ""
        for name, secret in list(self.users.items()):
            users += "%s," % name
        users.rstrip(",")

        for name, secret in list(self.secrets.items()):
            path = j.tools.path.get("%s/root/%s" % (self.root, name))
            path.mkdir_p()
            D2 = D.replace("$secret", secret)
            D2 = D2.replace("$name", name)
            C += D2

        C = C.replace("$root", self.root)
        C = C.replace("$users", users)
        C = C.replace("$port", str(self.port))

        j.tools.path.get("/etc/rsync/rsyncd.conf").write_text(C)

        path = j.tools.path.get("/etc/rsync/users")
        out = ""
        for name, secret in list(self.users.items()):
            out += "%s:%s\n" % (name, secret)

        path.write_text(out)

        path.chmod(0o600)

        # with bindmounts
        # cmd="mount | grep /tmp/server"

        # rc,out=j.sal.process.execute(cmd,die=False)
        # if rc==0:
        #     for line in out.split("\n"):
        #         if line=="":
        #             continue
        #         cmd="umount %s"%line.split(" ",1)[0]
        #         # print cmd
        #         j.sal.process.execute(cmd)

        # for name,passwd in self.secrets.iteritems():
        #     src="%s/download/%s"%(self.root,passwd)
        #     dest="%s/upload/%s"%(self.root,name)
        #     j.sal.fs.createDir(src)
        #     j.sal.fs.createDir(dest)
        #     # j.sal.fs.symlink(dest, src, overwriteTarget=True)

        #     cmd="mount --bind %s %s"%(src,dest)
        #     j.sal.process.execute(cmd)

    def start(self, background=False):
        self._log_info("start rsync server")
        if not j.core.tools.cmd_installed("rsync"):
            raise j.exceptions.Base("install rsync: 'j.servers.rsync.install()'")

        self.config_save()
        self.roles_prepare()

        self.startupcmd.start()

    def stop(self):
        self._log_info("stop rsync server")
        self.startupcmd.stop()

    @property
    def startupcmd(self):
        if not self._startupcmd:
            if not j.core.tools.cmd_installed("rsync"):
                raise j.exceptions.Base("cannot find command rsync, please install")
            cmd = "rsync -v --daemon --no-detach --config=/etc/rsync/rsyncd.conf"
            self._startupcmd = j.servers.startupcmd.get("rsync_%s" % self.name, cmd_start=cmd, ports=[self.port])
            self._startupcmd.executor = "tmux"

        return self._startupcmd

    def roles_prepare(self):
        for catpath in self.distrdir.dirs():
            for path in catpath.walkdirs():
                rolepath = path.joinpath(".roles")
                if rolepath.exists():
                    # found dir with role
                    relpath = path.lstrip(catpath)
                    roles = rolepath.text().strip()
                    roles = [item.strip() for item in roles.split(",")]
                    for role in roles:
                        destdir = self.rolesdir.joinpath(role, catpath.basename(), relpath)
                        self._log_debug(("link: %s->%s" % (path, destdir)))
                        path.symlink(destdir)
                        # j.sal.fs.createDir(destdir)
                        # for item in j.sal.fs.listFilesInDir(path, recursive=False, exclude=["*.pyc",".roles"], followSymlinks=False, listSymlinks=False):
                        #     relpath=j.sal.fs.pathRemoveDirPart(item,path)
                        #     destpathfile=j.sal.fs.joinPaths(destdir,relpath)
                        #     j.sal.fs.createDir(j.sal.fs.getDirName(destpathfile))
                        #     j.sal.fs.symlink(item, destpathfile, overwriteTarget=True)
