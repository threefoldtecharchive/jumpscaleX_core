import os
import uuid
from pprint import pprint

from Jumpscale import j

from .ZDBAdminClientBase import ZDBAdminClientBase
from .clients_impl import ZDBClientDirectMode, ZDBClientSeqMode, ZDBClientUserMode
from .clients_impl import ZDBClientDirectModeAdmin, ZDBClientSeqModeAdmin, ZDBClientUserModeAdmin

JSBASE = j.baseclasses.object


class ZDBClientFactory(j.baseclasses.object_config_collection_testtools):
    """

    different modes: seq,user,direct

    """

    __jslocation__ = "j.clients.zdb"
    _CHILDCLASS = None  # because we use _childclass_selector
    _SCHEMATEXT = """
    @url = jumpscale.zdb.client.1
    name** = "test" (S)
    addr = "localhost" (S)
    port = 9900 (I)
    secret_ = "" (S)
    nsname = "test" (S)
    admin = false (B)
    mode = "seq,user,direct" (E)

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
        elif jsxobject.mode == "direct":
            if jsxobject.admin:
                return ZDBClientDirectModeAdmin
            else:
                return ZDBClientDirectMode
        else:
            raise j.exceptions.Base("childclass cannot be defined")

    def client_admin_get(self, name="admin", addr="localhost", port=9900, secret="123456", mode="seq"):
        if self.exists(name=name):
            cl = self.get(name=name)
            # we should make sure AUTH has been launched as zdb client admin comes from config
            # and if we instanciated a new zdb server the AUTH command will not be executed
            cl.auth()
        else:
            cl = self.get(name=name, nsname=name, addr=addr, port=port, secret_=secret, mode=mode, admin=True)
        assert cl.admin == True
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

    def test(self):
        """
        kosmos 'j.clients.zdb.test()'

        """

        j.servers.zdb.test_instance_start()

        self.delete("admin")

        cl = self.client_admin_get(port=9901)
        assert cl.ping()

        self._test_run(name="base")
        self._test_run(name="admin")

        self.delete("admin")
        self.delete("test")
        self.delete("newnamespace")

        j.servers.zdb.test_instance_stop()
