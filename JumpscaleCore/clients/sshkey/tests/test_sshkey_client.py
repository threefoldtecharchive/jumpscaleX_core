import logging
import os.path
from Jumpscale import j
from subprocess import Popen, PIPE

sshkeyclient_name = ""
sshkey_dir = ""
sshkey_client = ""
ssh_pubkey = ""
ssh_pubkey = ""


def info(message):
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    logging.info(message)


def rand_string():
    return j.data.idgenerator.generateXCharID(10)


def before():
    global sshkeyclient_name, sshkey_dir, sshkey_client, ssh_pubkey, ssh_privkey
    sshkeyclient_name = "ssh_client_{}".format(rand_string())
    sshkey_dir = "{}/.ssh".format(j.core.myenv.config["DIR_HOME"])
    info("Create sshkey client with name {}".format(sshkeyclient_name))
    sshkey_client = j.clients.sshkey.get(name=sshkeyclient_name)
    ssh_pubkey = sshkey_client.pubkey
    ssh_privkey = sshkey_client.privkey


def after():
    sshkey_client.delete_from_sshdir()
    sshkey_client.delete()


# def test001_load_sshkey_client_into_database():
#     """
#     TC 469
#     Test to load sshkey client into database.
#
#     **Test scenario**
#     #. Create sshkey client.
#     #. Check the existence of the client in database, should be there.
#     #. Delete sshkey client from database.
#     #. Check the existence of the client in database, shouldn't be there.
#     #. Load sshkey client into database.
#     #. Check the existence of the client in database, should be there again.
#     """
#     info("Create sshkey client with name {}".format(sshkeyclient_name))
#     model = j.data.bcdb.system.model_get(url="jumpscale.sshkey.client")
#
#     assert model.get_by_name(name=sshkeyclient_name)
#     info("Delete sshkey files from database".format(sshkey_client))
#     sshkey_client.delete()
#     model = j.data.bcdb.system.model_get(url="jumpscale.sshkey.client")
#     with assertRaises(Exception) as error:
#         model.get_by_name(name=sshkeyclient_name)
#         assertTrue("cannot find data with name" in error.exception.args[0])
#     info("Load sshkey client into database")
#     sshkey_client.load_from_filesystem()
#     info("Check the existence of the client in database")
#     model = j.data.bcdb.system.model_get(url="jumpscale.sshkey.client")
#     assert model.get_by_name(name=sshkeyclient_name)


def test002_regenerate_sshkey():
    """
    TC 470
    Test to regenerate sshkey.

    **Test scenario**
    #. Create sshkey client, which generates public and private keys (pk1, priv_key1).
    #. Use generate method to regenerate the (public and private) keys, (pk2, priv_key2).
    #. Check that the keys have been regenerated, make sure that pk1 != pk2 and priv_key1 != priv_key2.
    """
    info("Use generate method to regenerate the (public and private) keys")
    sshkey_client.generate(reset=True)
    info("Check that the keys have been regenerated")
    assert os.path.isfile("{}/{}".format(sshkey_dir, sshkeyclient_name))
    assert os.path.isfile("{}/{}.pub".format(sshkey_dir, sshkeyclient_name))
    old_privkey = ssh_privkey
    new_privkey = open("{}/{}".format(sshkey_dir, sshkeyclient_name)).read()
    old_pubkey = ssh_pubkey
    new_pubkey = open("{}/{}".format(sshkey_dir, sshkeyclient_name)).read()
    assert old_pubkey != new_pubkey
    assert old_privkey != new_privkey


def test003_delete_sshkey_from_ssh_directory():
    """
    TC 473
    Test to delete sshkey files locally from ssh directory.

    **Test scenario**
    #. Create sshkey client.
    #. Use delete_from_sshdir to delete the sshkey client files from ssh directory.
    #. Check the existence of those files in the sshkey directory, shouldn't be there.
    """
    info("Use delete_from_sshdir to delete the sshkey client files from ssh directory")
    sshkey_client.delete_from_sshdir()
    info("Check the existence of those files in the sshkey directory, shouldn't be there")
    assert os.path.isfile("{}/{}.pub".format(sshkey_dir, sshkeyclient_name)) is False
    assert os.path.isfile("{}/{}".format(sshkey_dir, sshkeyclient_name)) is False


def test004_write_sshkey_files_into_ssh_directory():
    """
    TC 474
    Test to write sshkey files into ssh directory.

    **Test scenario**
    #. Create sshkey client.
    #. Check the existence of sshkey files (public [pk1] and private [priv_k1]) in ssh directory, should be there.
    #. Delete sshkey files from ssh directory.
    #. Use write_to_sshdir method to write sshkey again into the ssh directory.
    #. Check the existence of sshkey files in ssh directory, should be there.
    #. Check the public and private keys values, should be the same as (pk1, priv_k1).
    """
    info("Delete sshkey files from ssh directory")
    sshkey_client.delete_from_sshdir()
    info("Use write_to_sshdir method to write sshkey again into the ssh directory")
    sshkey_client.write_to_sshdir()
    info("Check the existence of sshkey files in ssh directory")
    assert os.path.isfile("{}/{}.pub".format(sshkey_dir, sshkeyclient_name))
    assert os.path.isfile("{}/{}".format(sshkey_dir, sshkeyclient_name))
    info("Check the public and private keys values")
    assert ssh_pubkey == open("{}/{}.pub".format(sshkey_dir, sshkeyclient_name)).read()
    assert ssh_privkey == open("{}/{}".format(sshkey_dir, sshkeyclient_name)).read()


def test005_load_sshkey_in_sshagent():
    """
    TC 475
    Test to load sshkey in sshagent.

    **Test scenario**
    #. Create sshkey client.
    #. Load sshkey in sshagent.
    #. Check that the sshkey has been loaded.
    """
    info("Load sshkey in sshagent")
    sshkey_client.load()
    info("Check if the ssh key has been loaded")
    _, output, error = j.sal.process.execute("ssh-add -l")
    assert "{}/{}".format(sshkey_dir, sshkeyclient_name) in output


def test006_unload_sshkey_from_sshagent():
    """
    TC 476
    Test to unload sshkey client from sshagent.

    **Test scenario**
    #. Create sshkey client.
    #. Unload the sshkey from sshagent.
    #. Check that the sshkey has been unloaded.
    """
    info("Unload the sshkey from sshagent")
    sshkey_client.unload()
    info("Check that sshkey has been unloaded")
    assert sshkey_client.is_loaded() is False
    _, output, error = j.sal.process.execute("ssh-add -l")
    assert sshkeyclient_name not in output


def test007_sshkey_is_loaded():
    """
    TC 477
    Test to check if the sshkey is loaded in the sshagent.

    **Test scenario**
    #. Create sshkey client.
    #. Load the sshkey in the sshagent.
    #. Check that the key has been loaded.
    #. Remove the sshkey from sshagent.
    #. Check that the key has been unloaded.
    """
    info("Load the sshkey in the sshagent")
    sshkey_client.load()
    info("Check that the key has been loaded")
    assert sshkey_client.is_loaded()
    info("Remove the sshkey from sshagent")
    sshkey_client.unload()
    info("Check that the key has been unloaded")
    assert sshkey_client.is_loaded() is False


def test008_get_public_key():
    """
    TC 478
    Test to get public key in sshkey client.

    **Test scenario**
    #. Create sshkey client, and get the public key (pk1).
    #. Check the public key for sshkey client (pk2) using pubkey_only method, should be the same as pk1.
    """
    info("Check the public key for sshkey client")
    ssh_key_pubkey_only = sshkey_client.pubkey_only
    pubkey_only = open("/{}/{}.pub".format(sshkey_dir, sshkeyclient_name)).read().split()[1]
    assert ssh_key_pubkey_only == pubkey_only
