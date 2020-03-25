from Jumpscale import j

"""
aim is to see if the subschema's are loaded properly in the metadata db
"""
skip = j.baseclasses.testtools._skip


def test_subschemas():
    """
    to run:
    kosmos 'j.data.bcdb.test(name="subschemas")'

    """

    schema = """

            @url = jsx.master.1
            cmds = (LO) !jsx.subschema.1
            cmd = (O) !jsx.subschema.2
            deepper = (O) !jsx.subschema.3


            @url = jsx.subschema.1
            name = ""
            comment = ""

            @url = jsx.subschema.2
            name2 = ""
            comment2 = ""

            @url = jsx.subschema.3
            name3 = ""
            comment3 = ""
            cmds = (LO) !jsx.subschema.3.1
            cmd = (O) !jsx.subschema.3.2

            @url = jsx.subschema.3.1
            name31 = ""
            comment31 = ""
            cmds = (LO) !jsx.subschema.3.1.1
            cmd = (O) !jsx.subschema.3.1.2

            @url = jsx.subschema.3.1.1
            name311 = ""
            comment311 = ""

            @url = jsx.subschema.3.1.2
            name312 = ""
            comment312 = ""

            @url = jsx.subschema.3.2.1
            name321 = ""
            comment321 = ""

            @url = jsx.subschema.3.2.2
            name322 = ""
            comment322 = ""


            @url = jsx.subschema.3.2
            name31 = ""
            comment31 = ""
            cmds = (LO) !jsx.subschema.3.2.1
            cmd = (O) !jsx.subschema.3.2.2

        """

    # bcdb = j.data.bcdb.get("test")
    bcdb, model = j.data.bcdb._test_model_get(type="sqlite")
    bcdb.reset()
    m = bcdb.model_get(schema=schema)

    urls = []
    urls.append("jsx.master.1")
    urls.append("jsx.subschema.1")
    urls.append("jsx.subschema.2")
    urls.append("jsx.subschema.3")
    urls.append("jsx.subschema.3.1")
    urls.append("jsx.subschema.3.1.1")
    urls.append("jsx.subschema.3.1.2")
    urls.append("jsx.subschema.3.2")
    urls.append("jsx.subschema.3.2.1")
    urls.append("jsx.subschema.3.2.2")

    for url in urls:
        md5 = j.data.schema.schemas_loaded[url]._md5
        s = bcdb.schema_get(md5=md5)  # need to start from bcdb
        assert s._md5 == md5
        assert s.url == url

    return "OK"
