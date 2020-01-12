from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.schema.test(name="changed")'
    """

    schema = """
        @url = jumpscale.schema.test11.a
        cmd = (O) !jumpscale.schema.test11.b
        cmds = (LO) !jumpscale.schema.test11.c
        j = (json)
        y = (yaml)
        d = (DICT)
        n = (N)
        e= "a,b" (E)
        color = "red"
        i = 1 (I)
        llist = (LS)

        @url = jumpscale.schema.test11.b
        something = ""
        deeper = (LO) !jumpscale.schema.test11.c

        @url = jumpscale.schema.test11.c
        name = ""
        comment = ""
        """

    s = j.data.schema.get_from_text(schema)
    assert s.props.cmd.is_jsxobject
    assert s.props.cmd.has_jsxobject
    assert not s.props.cmd.is_list
    assert s.props.cmds.has_jsxobject
    assert s.props.cmds.is_list
    assert s.props.cmds.is_list_jsxobject
    assert s.props.cmds.is_complex_type
    assert s.props.j.is_primitive_serialized
    assert s.props.y.is_primitive_serialized
    assert s.props.d.is_primitive_serialized
    assert s.props.d.is_primitive
    assert s.props.n.is_complex_type
    assert s.props.e.is_complex_type
    assert s.props.color.is_primitive
    assert not s.props.color.has_jsxobject
    assert not s.props.color.is_primitive_serialized
    assert not s.props.color.is_complex_type
    assert s.props.i.is_primitive
    assert not s.props.llist.is_primitive
    assert s.props.llist.is_complex_type
    assert s.props.llist.is_list

    o = s.new()
    assert o._changed
    assert o._changed_deserialized_items
    # lets now force the changed stat on False (of rootobj & subs)

    assert o.cmds.isjsxobject
    assert not o.llist.isjsxobject

    o._changed = False
    assert o._changed == False
    assert o.cmds._parent == o

    # some basic change tests
    o.i = 2
    assert o._changed == True
    o._changed = False
    assert o._changed == False

    o.e = "B"
    assert o._changed == True
    o._changed = False
    assert o._changed == False

    o.llist.new()
    assert o._changed == True
    o._changed = False
    assert o._changed == False

    o.j = [1, 2, 3]
    assert o._changed == True
    o._changed = False
    assert o._changed == False

    # 1 level deep
    o.cmd.something = "something data"
    assert o.cmd.something == "something data"
    assert o.cmd._changed
    assert o._changed

    ## 2levels deep
    o._changed = False
    assert o._changed == False
    a = o.cmd.deeper.new()
    a.comment = "aaa"
    assert o.cmd.deeper[0].comment == "aaa"
    assert o._changed
    assert o.cmd.deeper[0].comment == "aaa"
    assert o.cmd.deeper._parent == o.cmd
    assert o.cmd.deeper[0].comment == "aaa"
    assert o.cmd.deeper._root == o
    assert o.cmd.deeper[0].comment == "aaa"
    assert o.cmd.deeper[0]._parent == o.cmd
    assert o.cmd.deeper[0]._root == o
    o._changed = False
    assert o._changed == False
    assert o.cmd.deeper[0].comment == "aaa"

    # deep change
    a.comment = "aab"
    assert o._changed
    o._changed = False
    assert o._changed == False

    o._data
    assert o.cmd.deeper[0].comment == "aab"

    assert o._changed == False
    a.comment = "aac"
    assert a.comment == "aac"
    assert o.cmd.deeper[0].comment == "aac"

    bindata = o._data
    o2 = s.new(serializeddata=bindata)
    assert o2.cmd.deeper[0].comment == "aac"
    assert o2 == o

    # lets now remove the deserialized internal prop and see if it comes back ok
    o.serialize()
    assert o._deserialized_items == {}
    assert o._changed_deserialized_items == False
    assert o._changed == False
    assert o.cmd.deeper[0].comment == "aac"

    self._log_info("TEST DONE CHANGED")

    return "OK"
