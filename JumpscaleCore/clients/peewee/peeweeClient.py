import importlib
from Jumpscale import j

JSConfigClient = j.baseclasses.object_config


class PeeweeClient(JSConfigClient):
    _SCHEMATEXT = """
    @url = jumpscale.peewee.client
    name** = "" (S)
    ipaddr = "localhost" (S)
    port = 5432 (ipport)
    login = "postgres" (S)
    passwd_ = "" (S)
    dbname = "template" (S)
    dbtype = "postgres" (E)
    peeweeschema = "" (S)
    """

    def _init(self, **kwargs):
        self.passwd = self.passwd_
        self._peewee_model = None
        self._peewee = None

    @property
    def db(self):
        if not self._peewee:
            if self.dbtype == "postgres":
                from Jumpscale.clients.peewee.peewee import PostgresqlDatabase

                self._peewee = PostgresqlDatabase(
                    self.dbname, user=self.login, password=self.passwd_, host=self.ipaddr, port=self.port
                )
            else:
                raise j.exceptions.Base()
        return self._peewee

    def model_get(self):
        if not self._peewee_model:
            key = "%s_%s_%s_%s_%s" % (self.ipaddr, self.port, self.login, self.dbname, self.dbtype)

            cmd = 'pwiz.py -e postgresql -H %s -p %s   -u "%s"  -i %s' % (
                self.ipaddr,
                self.port,
                self.login,
                self.dbname,
            )
            print(cmd)
            rc, out, err = j.sal.process.execute(cmd, useShell=True, die=True, showout=False)
            path = j.sal.fs.joinPaths(j.dirs.TMPDIR, "peewee", key + ".py")
            j.sal.fs.createDir(j.sal.fs.joinPaths(j.dirs.TMPDIR, "peewee"))
            j.sal.fs.writeFile(path, out)
            loader = importlib.machinery.SourceFileLoader(key, path)
            module = loader.load_module(key)
            self._peewee_model = module

        return self._peewee_model
