from Jumpscale import j
from io import BytesIO
import binascii


def main(self):
    """
    kosmos -p 'j.servers.gedis.test("threebot_redis_registration_encryption")'
    """

    cl = self._threebot_client_default._redis  # is a client to a threebot server (in this test its local)

    # to make example complete, make sure we use json on our connection
    cl.execute_command("config_format", "json")

    """
    on server: the user_session can be authenticated and data can be verified, when verified it means 
    the data was encrypted and signed so the actor knows for sure that the source is real and data is correct
    user_session.authenticated
    user_session.data_verified
    """

    # login wih me
    seed = j.data.idgenerator.generateGUID()  # any seed works, the more random the more secure
    signature = j.data.nacl.default.sign_hex(seed)  # this is just std signing on nacl and hexifly it
    assert len(signature) == 128

    # authentication is done by means of threebotid and a random seed
    # which is signed with the threebot (is the client) private key
    res = cl.execute_command("auth", j.tools.threebot.me.default.tid, seed, signature)
    assert res == b"OK"
    error = False
    try:
        res = cl.execute_command("auth", j.tools.threebot.me.default.tid, seed + "a", signature)
    except:
        error = True
    assert error

    # lets now ask the threebot remote to load the right package using nothing else than redis
    # if there would be no authentication it would fail
    args = {}
    args["name"] = "ibiza_test"
    args["path"] = "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/examples/ibiza"

    data_return_json = cl.execute_command("default.package_manager.package_add", j.data.serializers.json.dumps(args))

    j.shell()

    #### LETS NOW TEST WITH ENCRYPTION

    # a threebotme is a local threebot definition, it holds your pubkey, ...
    # this returns 2 test nacl sessions & threebot definiions for a fake client & threebotserver
    nacl_client, nacl_server, threebot_me_client, threebot_me_server = j.tools.threebot.test_register_nacl_threebots()

    j.shell()

    print("**DONE**")
