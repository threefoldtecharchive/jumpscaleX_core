from Jumpscale import j
from io import BytesIO
import binascii


def main(self):
    """
    kosmos -p 'j.servers.gedis.test("threebot_redis_registration_encryption")'
    """

    # TODO:
    return

    #### LETS NOW TEST WITH ENCRYPTION

    # will register a threebot test.test & dummy.myself
    # returns the 2 nacls used in this test
    nacl1, nacl2, threebot1, threebot2 = j.clients.threebot.test()

    ##### NEXT STLL NEEDS TO BE DONE

    # to make example complete, make sure we use json on our connection
    cl.execute_command("config_format", "json")

    """
    on server: the user_session can be authenticated and data can be verified, when verified it means 
    the data was encrypted and signed so the actor knows for sure that the source is real and data is correct
    user_session.authenticated
    user_session.data_verified
    """

    seed = j.data.idgenerator.generateGUID()  # any seed works, the more random the more secure
    signature = nacl1.sign(seed)
    cl.execute_command("authenticate", seed, signature)

    j.shell()

    print("**DONE**")
