from Jumpscale import j
import random, requests, uuid, subprocess

skip = j.baseclasses.testtools._skip


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/552")
def before_all():
    pass


zdb = j.servers.zdb.get()
zdb = None


def info(message):
    j.tools.logger._log_info(message)


def rand_string(size=10):
    return str(uuid.uuid4()).replace("-", "")[1:10]


def before():
    global zdb
    zdb = j.servers.zdb.test_instance_start()


def after():
    j.servers.zdb.test_instance_stop()


def test_01_client_admin_get_and_client_get_and_destroy():
    """
    - Start zdb server .
    - Create namespace using client_admin_get.
    - Get zdb client and make sure it works correctly .
    - Destroy zdb server.
    - Check that server stopped and database removed successfully.
    """
    info("Create namespace using client_admin_get.")
    admin_client = zdb.client_admin_get()
    namespace = rand_string()
    result = admin_client.namespace_new(namespace)
    assert result.nsname == namespace

    info("Get zdb client and make sure it works correctly ")
    zdb_client = zdb.client_get(name=namespace, nsname=namespace)
    data = rand_string()
    id = zdb_client.set(data)
    assert id == 0
    assert data == zdb_client.get(id).decode()

    info(" Destroy zdb server")
    zdb.destroy()

    info("Check that server stopped and database removed successfully.")
    assert not j.sal.process.psfind("zdb")

    _, output, error = j.sal.process.execute("ls {DIR_BASE}/var/zdb", replace=True)
    assert zdb.name not in output
