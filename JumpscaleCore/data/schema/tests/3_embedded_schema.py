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

    kosmos 'j.data.schema.test(name="embedded_schema")'
    """

    def onelevel():

        schema0 = """
            @url = jumpscale.schema.test3.a
            cmd = (O) !jumpscale.schema.test3.b
            x = "1"
    
            @url = jumpscale.schema.test3.b
            name = ""
            comment = ""
            schemacode = ""
            """

        j.data.schema.get_from_text(schema0)
        so = j.data.schema.get_from_url(url="jumpscale.schema.test3.a")
        so2 = j.data.schema.get_from_url(url="jumpscale.schema.test3.b")
        o = so.new()
        o.x = "2"
        assert o._changed
        assert o.x == "2"

        assert o.cmd._changed == False
        o.cmd.name = "a"
        assert o.cmd._changed
        assert o.cmd.name == "a"
        assert o.cmd.comment == ""

        data = o.cmd._data
        subobj = j.data.serializers.jsxdata.loads(data)
        assert subobj.name == "a"

        data = o._data

        md5 = so._md5

        o2 = j.data.serializers.jsxdata.loads(data)

        print(o2)  # TODO: does not serialize well
        assert o2.cmd.name == "a"
        o3 = so.new(serializeddata=data)
        assert o3.cmd.name == "a"
        # CLEAN STATE

    # j.data.schema.remove_from_text(schema0)

    def onelevellist():

        schema1 = """
            @url = jumpscale.schema.test3.c
            cmds = (LO) !jumpscale.schema.test3.b
    
            @url = jumpscale.schema.test3.b
            name = ""
            comment = ""
            schemacode = ""
            """

        j.data.schema.get_from_text(schema1)
        so = j.data.schema.get_from_url(url="jumpscale.schema.test3.c")
        so2 = j.data.schema.get_from_url(url="jumpscale.schema.test3.b")
        o = so.new()

        cmd = o.cmds.new()
        cmd.name = "a"

        assert o.cmds[0].name == "a"

        assert o.cmds[0]._ddict == {"name": "a", "comment": "", "schemacode": ""}

        assert len(o.cmds) == 1

        data = o._data

        # to make sure after serialization is still ok
        assert o.cmds[0].name == "a"

        assert o.cmds[0]._ddict == {"name": "a", "comment": "", "schemacode": ""}

        assert len(o.cmds) == 1

        o2 = so.new(serializeddata=data)

        assert o2.cmds[0].name == "a"

        assert o2.cmds[0]._ddict == {"name": "a", "comment": "", "schemacode": ""}

        assert len(o2.cmds) == 1

        o3 = so.new(datadict=o._ddict)

        assert o3.cmds[0].name == "a"

        assert o3.cmds[0]._ddict == {"name": "a", "comment": "", "schemacode": ""}

        assert len(o3.cmds) == 1

        print(o)

        cmd = o.cmds.new()
        cmd.name = "cc"

        assert len(o.cmds) == 2
        assert o.cmds[1].name == "cc"
        # CLEAN STATE
        # j.data.schema.remove_from_text(schema1)

    onelevel()
    onelevellist()

    # more deep embedded (2 levels)

    schema2 = """
        @url = jumpscale.schema.test3.cmd
        name = ""
        comment = ""
        schemacode = ""

        @url = jumpscale.schema.test3.serverschema
        cmds = (LO) !jumpscale.schema.test3.cmdbox
        cmd = (O) !jumpscale.schema.test3.cmd

        @url = jumpscale.schema.test3.cmdbox
        cmd = (O) !jumpscale.schema.test3.cmd
        cmd2 = (O) !jumpscale.schema.test3.cmd
        
        """
    j.data.schema.get_from_text(schema2)  # just add
    schema_object2 = j.data.schema.get_from_url(url="jumpscale.schema.test3.serverschema")
    schema_object3 = j.data.schema.get_from_url(url="jumpscale.schema.test3.cmdbox")

    schema_test = schema_object2.new()

    for i in range(4):
        schema_object = schema_test.cmds.new()
        schema_object.name = "test%s" % i

    assert schema_test.cmds[2].name == "test2"
    schema_test.cmds[2].name = "test_two"
    assert schema_test.cmds[2].name == "test_two"

    bdata = schema_test._data

    print(schema_test._data)

    schema_test3 = schema_object3.new()
    schema_test3.cmd.name = "test"
    schema_test3.cmd2.name = "test"
    assert schema_test3.cmd.name == "test"
    assert schema_test3.cmd2.name == "test"

    bdata = schema_test3._data
    schema_test4 = schema_object3.new(serializeddata=bdata)
    assert schema_test4._ddict == schema_test3._ddict

    assert schema_test3._data == schema_test4._data

    self._log_info("TEST DONE SCHEMA EMBED")

    return "OK"
