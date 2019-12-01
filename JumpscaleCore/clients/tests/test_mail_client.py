import imaplib
import unittest
from Jumpscale import j
from testconfig import config
from base_test import BaseTest


@unittest.skip
class EmailClient(BaseTest):

    username = config["mail"]["username"]
    password = config["mail"]["password"]

    # @classmethod
    # def setUpClass(cls):
    #     cls.info("Start SMTP server in tmux using JSX")
    #     cmd = "kosmos 'j.servers.smtp.start()'"
    #     cls.info("Execute {} in tmux main session".format(cmd))
    #     cls.pan = j.servers.tmux.execute(cmd=cmd)
    #     cls.info("Wait for 30s to make sure that the server is running")
    #     sleep(30)

    def setUp(self):
        self.info("Create Mail client")
        self.RAND_STRING = self.rand_string()
        self.MAIL_CLIENT = j.clients.email.new(self.RAND_STRING, smtp_server="smtp.gmail.com", smtp_port=587)

    def tearDown(self):
        self.info("Delete Mail client")
        self.MAIL_CLIENT.delete()

    # @classmethod
    # def tearDownClass(cls):
    #     cls.info("Stop the running SMTP server")
    #     cls.pan.kill()

    def check_inbox(self, message_subject):
        """
        Check inbox in the mail to make sure that my message is sent.
        :param message_subject: message subject.
        """
        mail = imaplib.IMAP4_SSL("smtp.gmail.com")
        mail.login(self.username, self.password)
        mail.select("inbox")
        typ, data = mail.search(None, "ALL")
        mail_ids = data[0]
        id_list = mail_ids.split()
        latest_email_id = int(id_list[-1])
        for i in range(latest_email_id, latest_email_id - 10, -1):
            typ, data = mail.fetch(i, "(RFC822)")
            if message_subject in str(data):
                return True
            else:
                return False

    def test001_send_mail(self):
        """
        TC 567
        Test send method in mail client.

        **Test scenario**
        #. Send a message to email using send method in mail client.
        #. Make sure that message sent correctly.
        """
        # self.info("Check the SMTP server is running")
        # self.assertTrue(self.pan.cmd_running)

        self.info("Send a message to the server")
        RAND_NUM = self.rand_num()
        self.MAIL_CLIENT.send(
            self.username, subject="test_{}".format(RAND_NUM), message="test new message {}".format(RAND_NUM)
        )

        self.info("Make sure that message sent correctly")
        self.assertTrue(self.check_inbox("test_{}".format(RAND_NUM)))

    def test002_send_method_with_file_option(self):
        """
        TC 569
        Test send method with file attached.

        **Test scenario**
        #. Create a file locally under /tmp/.
        #. Send a message to email using send method in mail client with file attached.
        #. Make sure that message sent correctly, and check that file is attached.
        """
        RAND_NUM = self.rand_num()

        self.info("Create a file locally under /tmp/")
        with open("/tmp/test_{}".format(RAND_NUM), "a") as out:
            out.write("test mail client" + "\n")

        self.MAIL_CLIENT.send(
            self.username,
            subject="test_{}".format(RAND_NUM),
            message="test new message {}".format(RAND_NUM),
            files=["/tmp/test_{}".format(RAND_NUM)],
        )

        self.info("Make sure that message sent correctly, and check that file is attached")
        self.assertTrue(self.check_inbox("attachment; filename=test_{}".format(RAND_NUM)))
