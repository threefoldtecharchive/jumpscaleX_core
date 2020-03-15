from Jumpscale import j


def test_enums():
    """
    to run:

    kosmos 'j.data.schema.test(name="enums")'
    """
    j.data.schema.reset()
    schema_text1 = """
    @url = schema.test.enums1
    status = "init,config,installed" (E)
    category = 1,2,3 (E)
    """
    s1 = j.data.schema.get_from_text(schema_text1)

    schema_text2 = """
    @url = schema.test.enums2
    status = "halted,init,config,installed" (E)
    category = 0,1,2,3 (E)
    """
    s2 = j.data.schema.get_from_text(schema_text2)

    o1 = s1.new()
    assert o1.status == "init"
    assert o1.category == 1

    try:
        o1.status = "halted"
        raise ValueError("halted value is not an option in schema1 this should have raised an error")
    except:
        pass

    try:
        o1.category = 0
        raise ValueError("0 value is not an option in schema1 this should have raised an error")
    except:
        pass

    o2 = s2.new()
    assert o2.status == "halted"
    assert o2.category == 0

    o2.status = "init"
    o2.category = 1

    assert o2.status == o1.status
    assert o2.category == o1.category
    j.data.schema._log_info("TEST DONE FOR ENUMS")

    return "OK"
