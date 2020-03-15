import os
import uuid
from pprint import pprint

from Jumpscale import j

from .ZDBAdminClientBase import ZDBAdminClientBase
from .clients_impl import ZDBClientSeqMode, ZDBClientUserMode
from .clients_impl import ZDBClientSeqModeAdmin, ZDBClientUserModeAdmin

JSBASE = j.baseclasses.object


class ZDBClientFactory(j.baseclasses.object_config_collection_testtools):
    """

    different modes: seq,user

    """

    __jslocation__ = "j.clients.zdb"
    _CHILDCLASS = None  # because we use _childclass_selector
    _SCHEMATEXT = """
    @url = jumpscale.zdb.client.1
    name** = "test_instance" (S)
    addr = "localhost" (S)
    port = 9900 (I)
    secret_ = "" (S)
    nsname = "test" (S)
    admin = false (B)
    mode = "seq,user" (E)

    """

    def _childclass_selector(self, jsxobject, **kwargs):
        """
        allow custom implementation of which child class to use
        :return:
        """
        if jsxobject.mode == "seq":
            if jsxobject.admin:
                return ZDBClientSeqModeAdmin
            else:
                return ZDBClientSeqMode
        elif jsxobject.mode == "user":
            if jsxobject.admin:
                return ZDBClientUserModeAdmin
            else:
                return ZDBClientUserMode
        else:
            raise j.exceptions.Base("childclass cannot be defined")

    def client_admin_get(self, name="admin", addr="localhost", port=9900, secret=None, mode="seq"):
        cl = self.get(name=name, addr=addr, port=port, secret_=secret, mode=mode, admin=True)
        # we should make sure AUTH has been launched as zdb client admin comes from config
        # and if we instanciated a new zdb server the AUTH command will not be executed
        cl.auth()
        assert cl.admin is True
        assert self.exists(name=name)
        return cl

    def client_get(self, name="main", namespace=None, addr="localhost", port=9900, secret="1234", mode="seq"):
        """
        :param name: namespace name
        :param addr:
        :param port:
        :param secret:
        :return:
        """
        if not namespace:
            namespace = name
        cl = self.get(name=name, nsname=namespace, addr=addr, port=port, secret_=secret, mode=mode, admin=False)
        assert self.exists(name=name)
        return cl

    def test(self, name=""):
        """
        kosmos 'j.clients.zdb.test()'

        """
        zdb = j.servers.zdb.test_instance_start()
        cl = zdb.client_admin_get()
        assert cl.ping()
        self._tests_run(name=name)

        j.servers.zdb.test_instance_stop()
