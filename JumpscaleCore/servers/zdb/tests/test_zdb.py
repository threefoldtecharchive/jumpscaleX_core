from Jumpscale import j
from base_test import BaseTest
import random, requests, uuid, subprocess
from loguru import logger

LOGGER = logger
LOGGER.add("zdb_tests_{time}.log")

skip = j.baseclasses.testtools._skip
zdb = j.servers.zdb.get()


def info(message):
    LOGGER.info(message)


def os_command(command):
    info("Execute : {} ".format(command))
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = process.communicate()
    return output, error


def rand_string(size=10):
    return str(uuid.uuid4()).replace("-", "")[1:10]


def before():
    info("​Install zdb server.")
    j.servers.zdb.install()

    info("Start zdb server")
    zdb.start()


def test_01_client_admin_get_and_client_get_and_destroy():
    """
    - ​Install zdb server.
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
    zdb_client = zdb.client_get(nsname=namespace)
    data = rand_string()
    id = zdb_client.set(data)
    assert id == 0
    assert data == zdb_client.get(id).decode()

    info(" Destroy zdb server")
    zdb.destroy()

    info("Check that server stopped and database removed successfully.")
    output, error = os_command(" ps -aux | grep -v grep | grep startupcmd_zdb ")
    assert output.decode() == ""

    output, error = os_command(" ls {DIR_BASE}/var/zdb")
    assert zdb.name not in output.decode()
