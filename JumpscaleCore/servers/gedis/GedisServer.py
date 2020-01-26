import os
import signal
import sys

import gevent
from gevent import time
from gevent.pool import Pool
from gevent.server import StreamServer
from Jumpscale import j

from .GedisChatBot import GedisChatBotFactory
from .GedisCmds import GedisCmds
from .handlers import Handler

JSBaseConfig = j.baseclasses.object_config
from Jumpscale.tools.threebot_package.ThreeBotPackage import ThreeBotPackage

SCHEMA = """
@url = jumpscale.gedis.api
namespace = ""
name** = ""
cmds = (LO) !jumpscale.gedis.cmd
schemas = (LO) !jumpscale.gedis.schema

@url = jumpscale.gedis.cmd
name** = ""
comment = ""
schema_in_url = ""
schema_out_url = ""
args = (ls)
public = False

@url = jumpscale.gedis.schema
name** = ""
md5 = ""
url = ""
content = ""
"""


class Actors:
    pass


def waiter(job):
    while job.result is None:
        time.sleep(0.1)
    return job.result


class GedisServer(JSBaseConfig):
    _SCHEMATEXT = """
        @url = jumpscale.gedis.server
        name** = "main" (S)
        host = "0.0.0.0" (ipaddress)
        port = 9900 (ipport)
        ssl = False (B)
        secret_ = "" (S)
        ssl_keyfile = "" (S)
        ssl_certfile = "" (S)
        # actors_data = (LS)
        """

    def _init(self, **kwargs):
        self._sig_handler = []

        self.cmds_meta = {}  # is the metadata of the actor
        self.schema_urls = []  # used at python client side

        self.address = "{}:{}".format(self.host, self.port)

        self.web_client_code = None
        self.code_generated_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "gedis", self.name, "server")

        self.chatbot = GedisChatBotFactory()

        # self.namespaces = ["system", "default"]
        self._threebot_server = None

        j.data.schema.get_from_text(SCHEMA, newest=True)

        # hook to allow external servers to find this gedis
        # self.server_gedis = self

        # create dirs for generated codes and make sure is empty
        for cat in ["server", "client"]:
            code_generated_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "gedis", self.name, cat)
            j.sal.fs.remove(code_generated_dir)
            j.sal.fs.createDir(code_generated_dir)
            j.sal.fs.touch(j.sal.fs.joinPaths(code_generated_dir, "__init__.py"))

        # now add the one for the server
        if self.code_generated_dir not in sys.path:
            sys.path.append(self.code_generated_dir)

        for sig in [signal.SIGINT, signal.SIGTERM]:
            self._sig_handler.append(gevent.signal(sig, self.stop))

        self.handler = Handler(self)  # registers the current gedis server on the handler

    @property
    def gevent_server(self):
        if self.ssl:
            if not self.ssl_keyfile and not self.ssl_certfile:
                ssl_keyfile = j.core.tools.text_replace("{DIR_BASE}/cfg/ssl/resty-auto-ssl-fallback.key")
                ssl_certfile = j.core.tools.text_replace("{DIR_BASE}/cfg/ssl/resty-auto-ssl-fallback.crt")

                if j.sal.fs.exists(ssl_keyfile):
                    self.ssl_keyfile = ssl_keyfile
                if j.sal.fs.exists(ssl_certfile):
                    self.ssl_certfile = ssl_certfile

            if not self.ssl_keyfile and not self.ssl_certfile:
                self.ssl_keyfile, self.ssl_certfile = self.sslkeys_generate()

            else:
                if not j.sal.fs.exists(self.ssl_keyfile):
                    raise RuntimeError("SSL: Error keyfile not found")

                if not j.sal.fs.exists(self.ssl_certfile):
                    raise RuntimeError("SSL: Error certfile not found")

            self._log_info("Gedis SSL: using keyfile {0} and certfile {1}".format(self.ssl_keyfile, self.ssl_certfile))

            # Server always supports SSL
            # client can use to talk to it in SSL or not
            gedis_server = StreamServer(
                (self.host, self.port),
                spawn=Pool(),
                handle=self.handler.handle_gedis,
                keyfile=self.ssl_keyfile,
                certfile=self.ssl_certfile,
            )
        else:
            gedis_server = StreamServer((self.host, self.port), spawn=Pool(), handle=self.handler.handle_gedis)

        return gedis_server

    def actor_add(self, name, path, package):
        """
        add commands from 1 actor (or other python) file

        :param name:  each set of cmds need to have a unique name
        :param path: of the actor file
        :return:
        """
        assert name
        assert isinstance(package, ThreeBotPackage)

        if not j.sal.fs.exists(path):
            raise j.exceptions.Value("actor_add: cannot find actor at %s" % path)

        self._log_debug("actor_add:%s:%s", package.name, path)
        key = "%s.%s" % (package.name, name)
        self.cmds_meta[key] = GedisCmds(path=path, name=name, package=package)

    def actors_remove(self, name, package):
        assert name
        assert isinstance(package, ThreeBotPackage)

        key = "%s.%s" % (package.name, name)
        if key in self.cmds_meta:
            del self.cmds_meta[key]
            self._log_debug("actor_removed:%s:%s", package.name)

    ####################################################################

    def actors_list(self, threebotauthor="threebot", package="base"):
        """
        list all actors loaded in the server
        optinally filter base on namespace

        :return: list of actors
        :rtype: list
        """
        return list(self.cmds_meta.keys())

    def actors_methods_list(self, namespace="default"):
        """
        list the actors and their methods

        return a dict like:
        {
            'actor_name': {
                'schema': "str_schema",
                'cmds': {
                    "cmd_name1": "cmd1_args",
                    "cmd_name2": "cmd2_args",
                }
            }
        }

        :param namespace: if specified filer the actors based on the namespace used, defaults to "default"
        :param namespace: str, optional
        :return: dict of actor and they commands
        :rtype: dict
        """
        res = {}
        for key, actor in self.cmds_meta.items():
            res[actor.name] = {
                "schema": str(actor.data.schemas),
                "cmds": {cmd.name: str(cmd.args) for cmd in actor.cmds.values()},
            }
        return res

    ##########################CLIENT FROM SERVER #######################

    def client_get(self, namespace="default"):
        """
        Helper method to get a client that connect to this instance of the server

        it configure a client using the same info as the server.

        :param namespace: namespace to use, defaults to "default"
        :param namespace: str, optional
        :return: gedis client
        :rtype: GedisClient
        """

        data = {}
        if self.host == "0.0.0.0":
            host = "localhost"
        else:
            host = self.host
        data["host"] = host
        data["port"] = self.port
        data["password_"] = self.secret_
        data["namespace"] = namespace

        return j.clients.gedis.get(name=self.name, **data)

    def client_configure(self, namespace="default"):
        """
        Helper method to create a gedis client instance that connect to this instance of the server

        it configure a client using the same info as the server.

        :param namespace: namespace to use, defaults to "default"
        :param namespace: str, optional
        :return: gedis client
        :rtype: GedisClient
        """

        data = {"host": self.host, "port": self.port, "secret_": self.secret_, "ssl": self.ssl, "namespace": namespace}
        return j.clients.gedis.get(name=self.name, configureonly=True, **data)

    #######################PROCESSING OF CMDS ##############

    # def sslkeys_generate(self):
    #     if not self.ssl:
    #         raise j.exceptions.Base("sslkeys_generate: gedis server is not configure to use ssl")
    #
    #     path = os.path.dirname(self.code_generated_dir)
    #     key = j.sal.fs.joinPaths(path, "ca.key")
    #     cert = j.sal.fs.joinPaths(path, "ca.crt")
    #
    #     if os.path.exists(key) and os.path.exists(cert):
    #         return key, cert
    #
    #     j.sal.process.execute(
    #         'openssl req -newkey rsa:2048 -nodes -keyout ca.key -x509 -days 365 -out ca.crt -subj "/C=GB/ST=London/L=London/O=Global Security/OU=IT Department/CN=localhost"'.format(
    #             key, cert
    #         ),
    #         showout=False,
    #     )
    #
    #     # res = j.sal.ssl.ca_cert_generate(path)
    #     # if res:
    #     #     self._log_info("generated sslkeys for gedis in %s" % path)
    #     # else:
    #     #     self._log_info("using existing key and cerificate for gedis @ %s" % path)
    #     return key, cert

    # def load_actors(self):
    #     for item in self.actors_data:
    #         namespace, path = item.split(":")
    #         name = actor_name(path, namespace)
    #         key = actor_key(name, namespace)
    #         if key not in self.actors.keys():
    #             self.actor_add(path, namespace)
    #
    # def start(self):
    #     """
    #     this method is only used when not used in digitalme
    #     """
    #     # WHEN USED OVER WEB, USE THE DIGITALME FRAMEWORK
    #     self._log_info("start Server on {0} - PORT: {1}".format(self.host, self.port))
    #     self._log_info("%s RUNNING", str(self))
    #     self.gevent_server.serve_forever()
    #

    def stop(self):
        """
        stop receiving requests and close the server
        """
        # TODO: gracefull shutdown. wait for the greenlet to finish
        # since we start the server by passing it a gevent.Pool we can control
        # all the greenlet used by the server

        # prevent the signal handler to be called again if
        # more signal are received
        for h in self._sig_handler:
            h.cancel()

        self._log_info("stopping server")
        self.gevent_server.stop()

    def __repr__(self):
        return "<Gedis Server address=%s  generated_code_dir=%s)" % (self.address, self.code_generated_dir)

    __str__ = __repr__
