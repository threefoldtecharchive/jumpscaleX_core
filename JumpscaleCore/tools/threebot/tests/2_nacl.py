# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/
# In case TF TECH NV ceases to exist (e.g. because of bankruptcy)
#   then Incubaid NV also in Belgium will get the Copyright & Authorship for all changes made since July 2018
#   and the license will automatically become Apache v2 for all code related to Jumpscale & DigitalMe
# This file is part of jumpscale at <https://github.com/threefoldtech>.
# jumpscale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jumpscale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License v3 for more details.
#
# You should have received a copy of the GNU General Public License
# along with jumpscale or jumpscale derived works.  If not, see <http://www.gnu.org/licenses/>.
# LICENSE END


from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.bcdb.test(name="nacl")'

    """

    # simulate I am remote threebot
    client_nacl = ""  # TODO create a new nacl
    server_nacl = j.data.nacl.default  # (the one we have)

    server_tid = j.core.myenv.config["THREEBOT_ID"]
    client_tid = 99

    self._nacl = client_nacl
    data = [True, 1, [1, 2, "a"], jsxobject, "astring"]
    data_send_over_wire = self.serialize_sign_encrypt(data, pubkey_hex=server_nacl.pubkey)  # todo select right pubkey

    # client send the above to server

    # now we are server
    self._nacl = server_nacl

    # server just returns the info

    data_readable_on_server = self.deserialize_check_decrypt(data_send_over_wire, pubkey_hex=client_nacl.pubkey)
    # data has now been verified with pubkey of client

    assert data_readable_on_server == [True, 1, [1, 2, "a"], jsxobject._json, "astring"]

    # lets now return the data to the client

    data_send_over_wire_return = self.serialize_sign_encrypt(data, pubkey_hex=client_nacl.pubkey)

    # now we are client
    self._nacl = client_nacl
    # now on client we check
    data_readable_on_client = self.deserialize_check_decrypt(data_send_over_wire_return, pubkey_hex=server_nacl.pubkey)

    # back to normal
    self._nacl = server_nacl
    j.core.myenv.config["THREEBOT_ID"] = server_tid

    self._log_info("TEST NACL DONE")
    return "OK"
