import logging
import unittest
import subprocess
from Jumpscale import j


class BaseTest(unittest.TestCase):

    @staticmethod
    def info(message):
        logging.basicConfig(format='%(message)s', level=logging.INFO)
        logging.info(message)

    @staticmethod
    def os_command(command):
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = process.communicate()
        return output, error

    @staticmethod
    def rand_num():
        return j.data.idgenerator.generateRandomInt(100, 1000)

    @staticmethod
    def rand_string(num):
        return j.data.idgenerator.generateXCharID(num)

    def delete_client_method(self, client, schema_url, client_name):
        """
        This is method to test deleted in clients
        this method take a client_name and schema_url as an input and and delete it from BCDB.
        """
        self.info("check delete method on {} client".format(client_name))
        self.info("check the existence of the client in BCDB, it should be exist")
        model = j.data.bcdb.system.model_get(url=schema_url)
        if model.get_by_name(name=client_name):
            self.info("try to delete the client using delete method and check again, it shouldn't be exist")
            client.delete()
            self.info("check the existence of the client in BCDB")
            try:
                model.get_by_name(name=client_name)
            except Exception:
                pass
            return True
        else:
            return False
