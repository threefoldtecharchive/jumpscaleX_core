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

    kosmos 'j.data.schema.test(name="capnp_schema")'
    """
    schema0 = """
        @url = despiegk.test.group
        description = ""
        llist =  (LO) !despiegk.test.users
        listnum = (LI)
        """

    schema1 = """
        @url = despiegk.test.users
        nr = 4
        date_start = 0 (D)
        description = ""
        token_price = "10 USD" (N)
        cost_estimate = 0.0 (N) #this is a comment
        """

    o1_schema = j.data.schema.get_from_text(schema0)
    o2_schema = j.data.schema.get_from_text(schema1)

    o1 = o1_schema.new()

    print(o1_schema)

    print(o1_schema._capnp_schema)
    print(o2_schema._capnp_schema)

    o1.listnum.append("1")
    assert o1.listnum[0] == 1

    jsxobject = o1.llist.new()

    assert jsxobject.cost_estimate == 0.0
    assert jsxobject.cost_estimate == 0

    self._log_info("TEST DONE BASE")
    # CLEAN STATE
    # j.data.schema.remove_from_text(schema0)
    # j.data.schema.remove_from_text(schema1)
    self._log_info("TEST DONE CAPNP")

    return "OK"
