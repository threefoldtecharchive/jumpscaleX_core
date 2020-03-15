from Jumpscale import j


def test_load_from_dir():
    """
    to run:

    kosmos 'j.data.schema.test(name="load_from_dir")'
    """
    j.data.schema.reset()
    mpath = j.data.schema._dirpath + "/tests/schemas_toml"
    assert j.sal.fs.exists(mpath)

    j.data.schema.add_from_path(mpath)

    assert len(j.data.schema.schemas_loaded) == 4
    assert len(j.data.schema.schemas_loaded) == 4

    s = j.data.schema.get_from_url("threefoldtoken.wallet")

    assert len(s.properties_index_sql) == 1
    assert len(s.properties) == 5

    assert s.systemprops.importance == "true"
    assert len(s.systemprops) == 2

    s2 = j.data.schema.get_from_md5(s._md5)

    assert s2 == s

    s3 = j.data.schema.get_from_text(s2.text, newest=True)
    assert s2 == s3

    assert s2 == j.data.schema.get_from_url(s.url)

    j.data.schema._log_info("load from dir ok")
    # CLEAN STATE
    # j.data.schema.remove_from_text(s2.text)
