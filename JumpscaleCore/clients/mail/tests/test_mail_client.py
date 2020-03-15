import imaplib
import logging
from Jumpscale import j

j.builders.runtimes.python3.pip_package_install("nose-testconfig")
from testconfig import config

mail_client = ""
username = config["mail"]["username"]
password = config["mail"]["password"]


def info(message):
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    logging.info(message)


def rand_string():
    return j.data.idgenerator.generateXCharID(10)


def rand_num(start=100, stop=1000):
    return j.data.idgenerator.generateRandomInt(start, stop)


def before():
    info("Create Mail client")
    RAND_STRING = rand_string()
    global mail_client
    mail_client = j.clients.email.new(
        RAND_STRING, smtp_server="smtp.gmail.com", smtp_port=587, Email_from=username, password=password,
    )


def tearDown():
    info("Delete Mail client")
    mail_client.delete()


def check_inbox(data_query):
    """
    Check inbox in the email to make sure that my message has been sent correctly.
    :param data_query: message subject.
    """
    mail = imaplib.IMAP4_SSL("smtp.gmail.com")
    mail.login(username, password)
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


def test001_send_mail():
    """
    TC 567
    Test for sending a message to an email.

    **Test scenario**
    #. Send a message to an email using send method in mail client.
    #. Make sure that the message has been sent correctly.
    """

    info("Send a message to an email using send method in mail client")
    RAND_NUM = rand_num()
    mail_client.send(username, subject="test_{}".format(RAND_NUM), message="test new message {}".format(RAND_NUM))

    info("Make sure that the message has been sent correctly")
    assert check_inbox("test_{}".format(RAND_NUM))


def test002_send_method_with_file_option():
    """
    TC 569
    Test for sending an attached file to an email.

    **Test scenario**
    #. Create a file locally.
    #. Send a message to email using send method in mail client with file attached.
    #. Make sure that message has been sent correctly, and check the existing of the file.
    """
    RAND_NUM = rand_num()

    info("Create a file locally")
    with open("/tmp/test_{}".format(RAND_NUM), "a") as out:
        out.write("test mail client" + "\n")

    mail_client.send(
        username,
        subject="test_{}".format(RAND_NUM),
        message="test new message {}".format(RAND_NUM),
        files=["/tmp/test_{}".format(RAND_NUM)],
    )

    info("Make sure that message has been sent correctly, and check the existence of the file")
    assert check_inbox('attachment; filename="test_{}"'.format(RAND_NUM))
