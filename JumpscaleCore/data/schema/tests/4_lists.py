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

    kosmos 'j.data.schema.test(name="lists")'

    tests an issue with lists, they were gone at one point after setting a value

    test readonly behaviour

    """

    schema0 = """
        @url = jumpscale.schema.test4.cmd
        name = ""
        comment = ""        
        nr = 0
        """
    schemasub = j.data.schema.get_from_text(schema0)
    schemasub2 = j.data.schema.get_from_url(url="jumpscale.schema.test4.cmd")  # now get based on url
    assert schemasub2._md5 == schemasub._md5  # check we get the same schema back
    assert j.data.schema.get_from_md5(md5=schemasub._md5)._md5 == schemasub._md5

    assert schemasub2._md5 == j.data.schema._md5(schema0)

    schema1 = """
        @url = jumpscale.myjobs.job
        category*= ""
        time_start* = 0 (D)
        time_stop = 0 (D)
        state* = ""
        timeout = 0
        action_id* = 0
        args = ""   #json
        kwargs = "" #json
        result = "" #json
        error = ""
        return_queues = (LS)
        cmds = (LO) !jumpscale.schema.test4.cmd
        cmd = (O) !jumpscale.schema.test4.cmd
        
        """

    schema_object = j.data.schema.get_from_text(schema1)
    schema_object2 = j.data.schema.get_from_url(url="jumpscale.myjobs.job")  # now get based on url
    assert schema_object2._md5 == schema_object._md5  # check we get the same schema back
    assert j.data.schema.get_from_md5(md5=schema_object2._md5)._md5 == schema_object2._md5
    assert schema_object2._md5 == j.data.schema._md5(schema1)

    assert j.data.schema._url_to_md5["jumpscale.schema.test4.cmd"] == schemasub2._md5

    s5 = j.data.schema.get_from_url(url="jumpscale.schema.test4.cmd")
    assert s5._md5 == schemasub._md5

    q = schema_object.new()
    assert q.cmds._child_type_._schema._md5 == schemasub._md5

    qq = q.cmds.new()

    # check that the subschema corresponds to the right one
    assert qq._schema._md5 == schemasub._md5

    schema_test = schema_object.new()
    schema_test.return_queues = ["a", "b"]
    assert schema_test.return_queues.pylist() == ["a", "b"]
    assert schema_test.return_queues._inner_list == ["a", "b"]
    assert schema_test.return_queues == ["a", "b"]

    schema_test.return_queues[1] = "c"

    assert schema_test.return_queues.pylist() == ["a", "c"]
    assert schema_test.return_queues._inner_list == ["a", "c"]
    assert schema_test.return_queues == ["a", "c"]

    schema_test.return_queues.pop(0)
    assert schema_test.return_queues.pylist() == ["c"]
    assert schema_test.return_queues._inner_list == ["c"]
    assert schema_test.return_queues == ["c"]

    cmd = schema_test.cmds.new()
    cmd.name = "aname"
    cmd.comment = "test"
    cmd.nr = 10

    schema_test.cmd.name = "aname2"
    schema_test.cmd.nr = 11

    schema_test.category = "acategory"

    schema_test1 = {
        "category": "acategory",
        "time_start": 0,
        "time_stop": 0,
        "state": "",
        "timeout": 0,
        "action_id": 0,
        "args": "",
        "kwargs": "",
        "result": "",
        "error": "",
        "cmd": {"name": "aname2", "comment": "", "nr": 11},
        "return_queues": ["c"],
        "cmds": [{"name": "aname", "comment": "test", "nr": 10}],
    }

    schema_test._ddict

    assert schema_test._ddict["cmds"] == [{"name": "aname", "comment": "test", "nr": 10}]

    w = schema_test._ddict["cmds"][0]

    assert isinstance(w, dict)

    schema_test._data
    schema_test._json
    schema_test2 = schema_object.new(serializeddata=schema_test._data)
    # j.shell()
    assert schema_test._ddict == schema_test2._ddict
    assert schema_test._data == schema_test2._data

    assert schema_test._readonly == False

    # test we cannot change a subobj
    try:
        schema_test.category = "s"
    except Exception as e:
        assert str(e).find("object readonly, cannot set") != -1

    self._log_info("TEST DONE LIST")

    return "OK"
