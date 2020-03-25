import logging
from Jumpscale import j
from subprocess import Popen, PIPE

PATH = ""
sshkey_client = ""
SSHKEYCLIENT_NAME = ""


def info(message):
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    logging.info(message)


def rand_string():
    return j.data.idgenerator.generateXCharID(10)


def before():
    global SSHKEYCLIENT_NAME
    SSHKEYCLIENT_NAME = "ssh_client_{}".format(rand_string())
    info("Create sshkey client with name {}".format(SSHKEYCLIENT_NAME))

    global PATH
    PATH = "{}/.ssh/{}".format(j.core.myenv.config["DIR_HOME"], SSHKEYCLIENT_NAME)
    global sshkey_client
    sshkey_client = j.clients.sshkey.get(name=SSHKEYCLIENT_NAME, path=PATH)
    sshkey_client.save()

    info("Start ssh-agent")
    j.sal.process.execute("eval `ssh-agent -s`")

    info("Add sshkey to sshagent")
    j.sal.process.execute("ssh-add {}/.ssh/id_rsa".format(j.core.myenv.config["DIR_HOME"]))


def after():
    info("Delete sshkey files from ssh directory {}".format(SSHKEYCLIENT_NAME))
    sshkey_client.delete_from_sshdir()

    info("Delete sshkey client")
    sshkey_client.delete()


def test001_start_and_kill_sshagent():
    """
    TC 570
    Test start and kill ssh agent.

    **Test scenario**
    #. Start ssh agent client.
    #. Load ssh keys in sshagent.
    #. Check that ssh key is loaded.
    #. Try kill method in ssh agent client.
    #. Check that ssh key is unloaded.
    """
    info("Start ssh agent client")
    j.clients.sshagent.start()

    info("Load sshkey in sshagent")
    j.clients.sshagent.key_load(path=PATH, name=SSHKEYCLIENT_NAME)

    info("Check that ssh key is loaded")
    assert sshkey_client.is_loaded()

    info("Try kill method in ssh agent client")
    j.clients.sshagent.kill()

    info("Check that ssh key is unloaded")
    assert sshkey_client.is_loaded() is False


def test002_list_of_ssh_keys_in_sshagent():
    """
    TC 571
    Test to list of ssh keys in sshagent, and public key path.

    **Test scenario**
    #. Load sshkey in sshagent.
    #. Check if the ssh key is loaded using keys_list method.
    #. Check the public key path of the loaded ssh key using keypub_path_get method.
    """
    info("Load sshkey in sshagent")
    j.clients.sshagent.key_load(path=PATH, name=SSHKEYCLIENT_NAME)

    info("Check if the ssh key is loaded using keys_list method")
    assert PATH in j.clients.sshagent.keys_list()
    output = j.sal.process.execute("ssh-add -l")
    assert PATH in str(output)
