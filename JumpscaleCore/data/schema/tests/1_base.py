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

    kosmos 'j.data.schema.test(name="base")'
    """

    schema0 = """
        @url = despiegk.test
        llist = []
        llist2 = "" (LS) #L means = list, S=String
        llist3 = [1,2,3] (LF)
        nr = 4
        date_start = 0 (D)
        description = ""        
        description2 = (S)
        llist4 = [1,2,3] (L)
        llist5 = [1,2,3] (LI)
        llist6 = "1,2,3" (LI)
        U = 0.0
        nrdefault = 0
        nrdefault2 = (I)
        nrdefault3 = 0 (I)
        """

    schema_object = j.data.schema.get_from_text(schema_text=schema0)

    assert schema_object.url == "despiegk.test"
    print(schema_object)

    assert schema_object.property_llist.default.value == []
    assert schema_object.property_llist2.default.value == []
    assert schema_object.property_llist3.default.value == [1.0, 2.0, 3.0]
    # works with & without value
    assert schema_object.property_llist3.default == [1.0, 2.0, 3.0]
    assert schema_object.property_llist4.default == [1, 2, 3]
    assert schema_object.property_llist5.default == [1, 2, 3]
    assert schema_object.property_llist6.default == [1, 2, 3]

    ll = schema_object.property_llist3.jumpscaletype.default_get()
    assert ll.value == [1.0, 2.0, 3.0]

    assert (
        schema_object.property_llist3.js_typelocation == "j.data.types._types['list_281be192c3ea134b85dd0c368d7d1b36']"
    )

    o = schema_object.new()

    assert o.nrdefault == 0
    assert o.nrdefault2 == 2147483647
    assert o.nrdefault == 0
    assert o.description == ""
    assert o.description2 == ""

    assert o.llist3 == [1.0, 2.0, 3.0]

    o.llist2.append("yes")
    o.llist2.append("no")
    o.llist3.append(1.2)
    o.llist5.append(1)
    o.llist5.append(2)
    o.U = 1.1
    o.nr = 1
    o.description = "something"

    assert o.llist2 == ["yes", "no"]
    assert o.description == "something"
    assert o.llist3 == [1.0, 2.0, 3.0, 1.2]
    assert o.U == 1.1
    o.U = "1.1"
    assert o.U == 1.1

    # test the base serialization
    data = j.data.serializers.jsxdata.dumps(o)
    o2 = j.data.serializers.jsxdata.loads(data)
    assert o2 == o

    schema2 = """
        @url = despiegk.test2
        enum = "red,green,blue,zhisisaverylongoneneedittotestletsdosomemore" (E) #first one specified is the default one
        llist2 = "" (LS)
        nr = 4
        date_start = 0 (D)
        description = ""
        cost_estimate = 0.0 #this is a comment
        llist = []
        @url = despiegk.test3
        llist = []
        description = ""
        """

    j.data.schema.get_from_text(schema_text=schema2)

    s = j.data.schema.get_from_url(url="despiegk.test2")
    e = s.properties[0]  # is the enumerator
    assert e.js_typelocation != "j.data.types.enum"  # should not the default location

    schema_object1 = j.data.schema.get_from_url(url="despiegk.test2")
    schema_object2 = j.data.schema.get_from_url(url="despiegk.test3")

    o1 = schema_object1.new()
    o2 = schema_object2.new()
    o1.llist2.append("5")
    o1.llist2.append(6)

    assert "5" in o1.llist2
    assert "6" in o1.llist2

    c = o1._capnp_obj
    c2 = o1._capnp_obj

    assert c.llist2[0] == "5"
    assert c2.llist2[0] == "5"

    dd = o1._ddict

    assert dd["enum"] == 1
    assert dd["llist2"][1] == "6"
    assert dd["nr"] == 4

    o2.llist.append("1")

    assert o1.enum == "RED"
    assert o1._capnp_obj.enum == 1

    o1.enum = 2
    assert o1.enum == "GREEN"
    assert o1._capnp_obj.enum == 2
    o1.enum = "  green"
    assert o1.enum == "GREEN"
    assert o1.enum == " GREEN"
    assert o1.enum == " Green"

    assert o1._ddict_hr["enum"] == "GREEN"

    assert o1._capnp_obj.nr == 4
    assert o1._capnp_obj.llist2[0] == "5"

    assert o1._data.find(b"GREEN") == -1  # needs to be stored as int
    x = len(o1._data) + 0

    o1.enum = 4

    schema3 = """
        @url = despiegk.test2
        #lets check the defaults
        bool1 = true (B)
        bool2 = True (B)
        bool3 = false (B)
        bool4 = False (B)
        bool5 = 1 (B)
        bool6 = '1' (B)
        bool7 = '0' (B)
        bool8 = 'n' (B)
        int1 =  10 (I)
    """

    o = j.data.schema.get_from_text(schema3).new()

    assert o.bool1 == True
    assert o.bool2 == True
    assert o.bool3 == False
    assert o.bool4 == False
    assert o.bool5 == True
    assert o.bool6 == True
    assert o.bool7 == False
    assert o.bool8 == False
    assert o.int1 == 10

    schema4 = """
    @url = despiegk.doubletest
    name = ""
    llist = []    
    """
    s0 = j.data.schema.get_from_text(schema4)
    schema4prime = """
    @url = despiegk.doubletest
    name = ""
    llist = ""    
    """

    s1 = j.data.schema.get_from_text(schema4prime)

    assert s0._md5 != s1._md5

    s2 = j.data.schema.get_from_url(url="despiegk.doubletest")
    assert s2._md5 == s1._md5
    assert s2._md5 != s0._md5

    self._log_info("TEST DONE BASE")

    return "OK"
