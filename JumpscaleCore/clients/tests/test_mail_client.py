import imaplib
import unittest
from Jumpscale import j
from testconfig import config
from base_test import BaseTest


class MailClient(BaseTest):

    username = config["mail"]["username"]
    password = config["mail"]["password"]

    def setUp(self):
        self.info("Create Mail client")
        self.RAND_STRING = self.rand_string()
        self.mail_client = j.clients.email.new(
            self.RAND_STRING,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            Email_from=self.username,
            password=self.password,
        )

    def tearDown(self):
        self.info("Delete Mail client")
        self.mail_client.delete()

    def check_inbox(self, data_query):
        """
        Check inbox in the email to make sure that my message has been sent correctly.
        :param data_query: message subject.
        """
        mail = imaplib.IMAP4_SSL("smtp.gmail.com")
        mail.login(self.username, self.password)
        mail.select("inbox")
        status, data = mail.search(None, "ALL")
        mail_ids = data[0]
        id_list = mail_ids.split()
        latest_email_id = int(id_list[-1])
        for i in range(latest_email_id, latest_email_id - 10, -1):
            status, data = mail.fetch(str(i), "(RFC822)")
            if data_query in str(data[0][1]):
                return True
        return False

    def test001_send_mail(self):
        """
        TC 567
        Test for sending a message to an email.

        **Test scenario**
        #. Send a message to an email using send method in mail client.
        #. Make sure that the message has been sent correctly.
        """

        self.info("Send a message to an email using send method in mail client")
        RAND_NUM = self.rand_num()
        self.mail_client.send(
            self.username, subject="test_{}".format(RAND_NUM), message="test new message {}".format(RAND_NUM)
        )

        self.info("Make sure that the message has been sent correctly")
        self.assertTrue(self.check_inbox("test_{}".format(RAND_NUM)))

    def test002_send_method_with_file_option(self):
        """
        TC 569
        Test for sending an attached file to an email.

        **Test scenario**
        #. Create a file locally.
        #. Send a message to email using send method in mail client with file attached.
        #. Make sure that message has been sent correctly, and check the existing of the file.
        """
        RAND_NUM = self.rand_num()

        self.info("Create a file locally")
        with open("/tmp/test_{}".format(RAND_NUM), "a") as out:
            out.write("test mail client" + "\n")

        self.mail_client.send(
            self.username,
            subject="test_{}".format(RAND_NUM),
            message="test new message {}".format(RAND_NUM),
            files=["/tmp/test_{}".format(RAND_NUM)],
        )

        self.info("Make sure that message has been sent correctly, and check the existing of the file")
        self.assertTrue(self.check_inbox('attachment; filename="test_{}"'.format(RAND_NUM)))
