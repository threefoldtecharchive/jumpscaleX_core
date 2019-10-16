from JumpscaleCore.servers.tests.base_test import BaseTest
from Jumpscale import j
from smtplib import SMTP
from imbox import Imbox
from imapclient import IMAPClient


class TestSMTPIMAP(BaseTest):
    def test001_check_smtp_save_message_in_bcdb(self):
        """
        SMTP server should connect to 'main' bcdb instance and store data into it.

        steps:
            - Start SMTP server in tmux
            - Connect to the server, should succeed.
            - Send a message to the server, should succeed.
            - Check the database, Should have the message.
        :return:
        """
        cmd = "kosmos 'j.servers.smtp.start()'"
        self.info("Execute {} in tmux main session".format(cmd))
        pan = j.servers.tmux.execute(cmd=cmd)
        self.info("Assert that the server is running")
        self.assertTrue(pan.cmd_running)

        self.info("Connect to the server 0.0.0.0:7002")
        with SMTP("0.0.0.0", 7002) as smtp:
            body = "Hello!"
            from_mail = "test@mail.com"
            to_mail = "target@example.com"
            msg = ("From: %s\r\nTo: %s\r\n\r\n" % (from_mail, to_mail)) + body
            smtp.sendmail(from_mail, to_mail, msg)

        self.info("Get the data from the database")
        db = j.data.bcdb.get("mails")
        retrieved_model = db.model_get(url="jumpscale.email.message")
        data = retrieved_model.find()[-1]

        self.info("Assert that the message has been saved in the database")
        self.assertEqual(data.from_email, "you@gmail.com")
        self.assertEqual(data.to_email, "target@example.com")
        self.assertEqual(data.body, body)

        self.info("Destroy the database")
        db.destroy()
        self.info("Stop the running server")
        pan.kill()

    def test002_imapclient_can_create_folder_in_imap(self):
        """
        Client can create folders in his mail.

        Steps:
        - Start imap server, should succeed.
        - List default folder, inbox should be there.
        - Create new folder, should succeed.
        """
        cmd = "kosmos 'j.servers.imap.start()'"
        self.info("Execute {} in tmux main session".format(cmd))
        pan = j.servers.tmux.execute(cmd=cmd)
        self.info("Assert that the server is running")
        self.assertTrue(pan.cmd_running)

        self.info("List default folder, inbox should be there")
        box = Imbox("0.0.0.0", "random@mail.com", "randomPW", ssl=False, port=7143)
        self.assertIn("INBOX", box.folders()[-1])

        self.info("Connect the client to the IMAP server")
        client = IMAPClient("0.0.0.0", port=7143, ssl=False)
        client.login("random@mail.com", "randomPW")

        box_name = self.rand_string()
        self.info("Create {} box".format(box_name))
        client.create_folder(box_name)

        self.info("Assert that the new box has been created")
        self.assertIn(box_name, box.folders()[-1])

        self.info("Stop the running server")
        pan.kill()

    def test003_imapClient_get_messages_from_database(self):
        """
         Client can create folders in his mail.

           Steps:
           - Start smtp server, shoud success.
           - Send message to smtp server.
           - Start imap server, should succeed.
           - List default folder, inbox should be there.
           - Client should get the message from the database.
        """
        cmd = "kosmos 'j.servers.smtp.start()'"
        self.info("Execute {} in tmux main session".format(cmd))
        pan = j.servers.tmux.execute(cmd=cmd)
        self.info("Assert that the server is running")
        self.assertTrue(pan.cmd_running)

        self.info("Connect to the server 0.0.0.0:7002")
        with SMTP("0.0.0.0", 7002) as smtp:
            body = "Hello!"
            from_mail = "test@mail.com"
            to_mail = "target@example.com"
            msg = ("From: %s\r\nTo: %s\r\n\r\n" % (from_mail, to_mail)) + body
            smtp.sendmail(from_mail, to_mail, msg)

        cmd = "kosmos 'j.servers.imap.start()'"
        self.info("Execute {} in tmux main session".format(cmd))
        pan_imap = j.servers.tmux.execute(cmd=cmd)
        self.info("Assert that the server is running")
        self.assertTrue(pan.cmd_running)

        self.info("Connect to the imap server")
        box = Imbox("0.0.0.0", "random@mail.com", "randomPW", ssl=False, port=7143)

        uid, last_message = box.messages()[-1]
        self.info("Assert that client get the message from the database")
        self.assertEqual(last_message.sent_from[0]["email"], "you@gmail.com")
        self.assertEqual(last_message.sent_to[0]["email"], "target@example.com")
        self.assertEqual(last_message.subject, body)

        self.info("Stop the running server")
        pan.kill()
        pan_imap.kill()
