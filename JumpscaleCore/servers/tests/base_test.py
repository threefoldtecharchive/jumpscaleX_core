import unittest
import subprocess, uuid
from loguru import logger


class BaseTest(unittest.TestCase):
    LOGGER = logger
    LOGGER.add("server_{time}.log")
    SERVERS = [
        "corex",
        "mail_forwarder",
        "etcd",
        "zdb",
        "odoo",
        "sonic",
        "sanic",
        "startupcmd",
        "capacity",
        "flask",
        "errbot",
        "gedis_websocket",
        "sockexec",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def info(self, message):
        BaseTest.LOGGER.info(message)

    def os_command(self, command):
        self.info("Execute : {} ".format(command))
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = process.communicate()
        return output, error

    def set_database_data(self, database):
        database.name = str(uuid.uuid4()).replace("-", "")[1:10]
        database.admin_email = "{}@example.com".format(database.name)
        database.admin_passwd_ = str(uuid.uuid4()).replace("-", "")[1:10]
