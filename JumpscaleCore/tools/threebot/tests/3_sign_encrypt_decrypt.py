from Jumpscale import j
import nacl.secret
import nacl.utils
import base64
import hashlib
from nacl.public import PrivateKey, SealedBox
from nacl.signing import SigningKey, VerifyKey
import binascii
from unittest import TestCase


def main(self):
    """
    to run:

    kosmos 'j.tools.threebot.test(name="sign_encrypt_decrypt")'

    """
    # here is how the keys are used
    #   private    /      public    /  crypto algo  / good for
    # signing_key  /    verify_key  /  ed 25119     / signature
    # private_key  /    public_key  / curve 25119   / encryption
    # all the keys derives from signing_key
    # e.g. private_key = signing_key.to_curve25519_private_key()
    #

    test_case = TestCase()
    data_list = self._get_test_data()
    # seed = j.data.encryption.mnemonic_to_seed(j.data.encryption.mnemonic_generate())
    server_sk = j.data.nacl.default
    # test asymetric encryptoin between 2 users
    client_sk = nacl.public.PrivateKey.generate()
    print("*******server_pubkey:%s" % server_sk.public_key.encode())
    print("*******client_pubkey:%s " % client_sk.public_key.encode())
    # this key should not be the same as the one in store
    assert client_sk.public_key.encode() != server_sk.public_key.encode()
    assert client_sk.public_key.encode() != server_sk.verify_key.encode()

    tid = j.tools.threebot.me.default.tid

    self._log_info("sign arbitrary data should work and be verified with 3bot pub key")
    res = self._serialize_sign_encrypt(data_list, serialization_format="json", pubkey_hex=None)
    assert len(res) == 3
    # threebot should send its id
    assert res[0] == tid
    threebot_sign = res[2]
    # threebot sign should be valid
    sign_data_raw = self._serialize(data_list, serialization_format="json").encode()
    assert sign_data_raw == res[1]
    assert server_sk.verify(sign_data_raw, threebot_sign)
    # make sure we are using the server_sk signing pubkey
    assert server_sk.verify(sign_data_raw, threebot_sign, verify_key=server_sk.verify_key.encode())

    self._log_info("verify signature with client pubkey should fail")
    assert not server_sk.verify(sign_data_raw, threebot_sign, verify_key=client_sk.public_key.encode())

    self._log_info("sign and encrypt arbitrary data should work and be verified with 3bot pub key")
    res = self._serialize_sign_encrypt(
        data_list, serialization_format="msgpack", pubkey_hex=binascii.hexlify(client_sk.public_key.encode())
    )
    # verify the encoding decoding of the pubkey
    assert (
        client_sk.public_key.encode()
        == nacl.public.PublicKey(binascii.unhexlify(binascii.hexlify(client_sk.public_key.encode()))).encode()
    )
    # threebot should send its id
    assert res[0] == tid
    threebot_sign = res[2]
    # threebot sign should be valid
    sign_data_raw = self._serialize(data_list, serialization_format="msgpack")
    assert server_sk.verify(sign_data_raw, threebot_sign)
    # client shoudl be abe to decrypt the data
    decrypted = j.data.nacl.default.decrypt(res[1], private_key=client_sk)
    assert sign_data_raw == decrypted

    self._log_info("decrypt data with 3bot priv key should fail")
    with test_case.assertRaises(Exception) as cm:
        decrypted = j.data.nacl.default.decrypt(res[1], private_key=server_sk.private_key)
    ex = cm.exception
    assert "An error occurred trying to decrypt the message" in str(ex.args[0])

    self._log_info("3bot should be able to decrypt a payload and verify a signature against a pubkey")
    # create a  payload  for the 3bot from the client
    data_raw = self._serialize(data_list, serialization_format="msgpack")
    # as it is for the 3bot we will encrypt it with the 3bot pubkey
    data_enc = j.data.nacl.default.encrypt(data_raw, public_key=server_sk.public_key)
    # as it is from the client we sign the payload before encryption with the client priv key
    # p = PrivateKey(client_sk)
    client_sign_k = SigningKey(client_sk.encode())
    signature = client_sign_k.sign(data_raw).signature
    # b"\xe8\xa1\xf8\x93\xf0\xca\x00\x0cZa\x11\x82\x8d\x018\xe2{'\xf1\x1b\xb3\x9dD\xde\xa1Y\xb3\xe0\xbc\xdd \xd5"
    client_verif_k = client_sign_k.verify_key
    p = server_sk.verify(data_raw, signature, verify_key=client_verif_k)

    # let's choose an arbitrary 3bot id for the client
    client_bot = "sarah.connor"
    payload = [client_bot, data_enc, signature]
    res = self._deserialize_check_decrypt(
        payload, serialization_format="msgpack", verifykey_hex=binascii.hexlify(client_verif_k.encode())
    )
    assert len(res) == len(data_list)
    assert res[0] == data_list[0]

    self._log_info("decrypt a payload and verify a signature against an incorrect pubkey should fail")

    with test_case.assertRaises(Exception) as cm:
        res = self._deserialize_check_decrypt(
            payload,
            serialization_format="msgpack",
            verifykey_hex=binascii.hexlify(nacl.public.PrivateKey.generate().public_key.encode()),
        )
    ex = cm.exception

    assert "could not verify signature" in str(ex.args[0])

    self._log_info("decrypt a payload encrypted with an incorrect pubkey should fail")
    tmp_sk = nacl.public.PrivateKey.generate()
    #  we will encrypt it with a tmp pubkey
    data_wrong_enc = j.data.nacl.default.encrypt(data_raw, public_key=tmp_sk.public_key)
    payload = [client_bot, data_wrong_enc, signature]
    with test_case.assertRaises(Exception) as cm:
        res = self._deserialize_check_decrypt(
            payload, serialization_format="msgpack", verifykey_hex=binascii.hexlify(client_sk.public_key.encode())
        )
    ex = cm.exception
    assert "An error occurred trying to decrypt the message" in str(ex.args[0])

    # CLEAN STATE
    self._log_info("TEST sign_encrypt_decrypt DONE")
    return "OK"
