import logging
import unittest
from subprocess import Popen, PIPE
from Jumpscale import j


class BaseTest(unittest.TestCase):
    @staticmethod
    def info(message):
        logging.basicConfig(format="%(message)s", level=logging.INFO)
        logging.info(message)

    @staticmethod
    def os_command(command):
        process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
        output, error = process.communicate()
        return output, error

    @staticmethod
    def rand_num(start=100, stop=1000):
        return j.data.idgenerator.generateRandomInt(start, stop)

    @staticmethod
    def rand_string():
        return j.data.idgenerator.generateXCharID(10)

    def delete_client_method(self, client, schema_url, client_name):
        """
        This is method to test delete method in clients
        this method take a client_name and schema_url as an input and and delete it from BCDB.
        """
        self.info("Delete {} client from database".format(client_name))
        model = j.data.bcdb.system.model_get(url=schema_url)
        if model.get_by_name(name=client_name):
            self.info("Delete the client from the database using delete method")
            client.delete()
            self.info("Check the existence of {} client in the database".format(client_name))
            try:
                model.get_by_name(name=client_name)
            except Exception:
                pass
            return True
        else:
            return False
