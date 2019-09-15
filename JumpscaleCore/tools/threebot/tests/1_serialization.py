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

    kosmos 'j.data.bcdb.test(name="serialization")'

    """

    data_list = self.get_test_data()
    res_j = self.serialize(data_list, serialization_format="json")
    print(res_j)
    assert (
        res_j
        == '[42, 5.6, "lorem ipsum gloria dea alea jacta es", "{\\"a\\": 1, \\"yolo\\": \\"yeeh\\"}", "[\\"uouo\\", {\\"a\\": 1, \\"yolo\\": \\"yeeh\\"}]"]'
    )
    res_mp = self.serialize(data_list, serialization_format="msgpack")
    print(res_mp)
    assert (
        res_mp
        == b"\x95*\xcb@\x16ffffff\xd9$lorem ipsum gloria dea alea jacta es\xc4\x0e\x82\xa1a\x01\xa4yolo\xa4yeeh\xc4\x14\x92\xa4uouo\x82\xa1a\x01\xa4yolo\xa4yeeh"
    )

    un_res_mp = self.unserialize(res_mp, serialization_format="msgpack")
    print(un_res_mp)

    assert un_res_mp == data_list

    un_res_j = self.unserialize(res_j, serialization_format="json")
    print(un_res_j)

    for idx, val in enumerate(data_list):
        if not val == un_res_j[idx]:
            assert val.__str__() == un_res_j[idx].replace('"', "'")

    # CLEAN STATE
    self._log_info("TEST serialization DONE")
    return "OK"
