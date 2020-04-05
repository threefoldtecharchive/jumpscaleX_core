from Jumpscale import j

try:
    from parameterized import parameterized
except ImportError:
    j.builders.runtimes.python3.pip_package_install("parameterized", reset=True)
    from parameterized import parameterized
import logging

skip = j.baseclasses.testtools._skip


def before_all():
    # try:
    addRegistryPackage()
    # except Exception:
    # after_all()
    # raise


# def after_all():
#   j.servers.threebot.default.stop()
#   j.sal.process.killall("tmux")


def info(message):
    j.tools.logger._log_info(message)


def addRegistryPackage():
    # . Start threebot server, add registery package, then reload the client.
    j.servers.threebot.local_start_3bot(background=True)
    gedis_cl = j.clients.gedis.get("pm", port=8901, package_name="zerobot.packagemanager")
    gedis_cl.actors.package_manager.package_add(
        path="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/registry"
    )
    gedis_cl.reload()
    return gedis_cl


def getNewUser():
    tid = j.data.idgenerator.generateRandomInt(1000, 9000)
    randStr = j.data.idgenerator.generateXCharID(10)
    return j.me_identities.me.get(randStr, tid=tid, email=randStr + "@test.com", tname=randStr + "_name")


def getSchemaAndModel(x="hello"):
    schema = """
        @url = threebot.registry.test.schema.1
        url = ""
        x = ""
        tags = (LS)
    """
    randStr = j.data.idgenerator.generateXCharID(10)
    scm = j.data.schema.get_from_text(schema)
    model = j.clients.bcdbmodel.get(url=scm.url).new()
    model.url = randStr + ".com"
    model.x = x
    model.save()
    return schema, model


def register_using_filter(filter, **kwargs):
    filter_value = j.data.idgenerator.generateRandomInt(1000, 2000)

    if filter == "country_code":
        j.clients.tfgrid_registry.register(country_code=filter_value, **kwargs)

    elif filter == "topic":
        filter_value = "TRAVEL"
        j.clients.tfgrid_registry.register(country_code="234", topic=filter_value, **kwargs)

    elif filter == "location_latitude":
        j.clients.tfgrid_registry.register(country_code="234", location_latitude=filter_value, **kwargs)

    else:
        j.clients.tfgrid_registry.register(country_code="234", location_longitude=filter_value, **kwargs)

    return filter_value


def find_using_filter(filter, filter_value):

    if filter == "country_code":
        res = j.clients.tfgrid_registry.find_formatted(registered_info_format="yaml", country_code=filter_value)

    elif filter == "topic":
        res = j.clients.tfgrid_registry.find_formatted(registered_info_format="yaml", topic=filter_value)

    elif filter == "location_latitude":
        res = j.clients.tfgrid_registry.find_formatted(registered_info_format="yaml", location_latitude=filter_value)

    else:
        res = j.clients.tfgrid_registry.find_formatted(registered_info_format="yaml", location_longitude=filter_value)

    data = j.data.serializers.yaml.loads(res)
    return data


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/484")
def test001_RegisterationAndPrivacy():
    """TC560
    #. Start threebot server, add registery package, then reload the client.
    #. Register user1's data as public, should succeed
    #. Get user1's public data, should succeed
    #. Register user1's data as private with giving access to user2, should succeed
    #. Get data with user 2, should succeed
    #. Get data with unauthorized data, should not be able to get the data
    """

    country_code = j.data.idgenerator.generateXCharID(10)
    schema, model = getSchemaAndModel()
    author = getNewUser()
    authorized_reader = getNewUser()
    unauthorized_reader = getNewUser()

    info("Register user1's data as public, should succeed")
    data_id1 = j.clients.tfgrid_registry.register(
        schema=schema, authors=[author.tid], model=model, is_encrypted_data=False, country_code=country_code
    )
    assert data_id1  # msg = "Failed to register content"

    info("Get user1's public data, should succeed")
    data = j.clients.tfgrid_registry.get_data_by_id(data_id1, author.tid)
    assert model == data

    info("Register user1's data as private with giving access to user2, should succeed")
    data_id2 = j.clients.tfgrid_registry.register(
        schema=schema,
        authors=[author.tid],
        model=model,
        is_encrypted_data=True,
        readers=[authorized_reader.tid],
        country_code=country_code,
    )
    assert data_id2  # msg = "Failed to register content"

    info("Get data with user 2, should succeed")
    data = j.clients.tfgrid_registry.find_encrypted(authorized_reader.tid)
    assert model == data[-1]

    info("Get data with unauthorized data, should not be able to get the data")
    data = j.clients.tfgrid_registry.find_encrypted(unauthorized_reader.tid)
    assert not data


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/484")
def test002_CheckOnDataFormat():
    """TC561
    #. Start threebot server, add registery package, then reload the client.
    #. Register user1's data
    #. Check if you can load the data in json format, should succeed
    #. Check if you can load the data in yaml format, should succeed
    """

    info("Register user1's data as public")
    schema, model = getSchemaAndModel()
    author = getNewUser()
    data_id1 = j.clients.tfgrid_registry.register(
        schema=schema, authors=[author.tid], model=model, is_encrypted_data=False, country_code="2354"
    )

    assert data_id1  # msg = "Failed to register your content"

    info("Check if you can return the data in json format, should succeed")
    res = j.clients.tfgrid_registry.find_formatted(registered_info_format="json")
    data = j.data.serializers.json.loads(res)
    assert data

    info("Check if you can return the data in yaml format, should succeed")
    res = j.clients.tfgrid_registry.find_formatted(registered_info_format="yaml")
    data = j.data.serializers.yaml.loads(res)
    assert data


@parameterized.expand(["country_code", "location_latitude", "location_longitude"])
@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/484")
def test003_search_using_single_filter(filter):
    """TC562
    #. Start threebot server, add registery package, then reload the client.
    #. Register user1's data (D1) with adding filter
    #. Get the data using that filter, should succeed
    #. Register user1's different data (D2) with adding same filter
    #. Get data using filter F1, should return D1 and D2
    """

    info("Register user1's data (D1) with adding filter")
    x = j.data.idgenerator.generateXCharID(10)
    schema, model = getSchemaAndModel(x)
    author = getNewUser()
    filter_value = register_using_filter(filter, schema=schema, authors=[author.tid], model=model)

    info("Get the data using that filter, should succeed")
    data = find_using_filter(filter, filter_value)
    assert len(data) == 1  # msg: "couldn't filter using country code")
    assert data[0]["x"] == x

    info("Register user1's different data (D2) with adding same filter")
    x2 = j.data.idgenerator.generateXCharID(10)
    schema, model = getSchemaAndModel(x2)
    filter_value = register_using_filter(filter, schema=schema, authors=[author.tid], model=model)

    info("Get data using filter F1, should return D1 and D2")
    data2 = find_using_filter(filter, filter_value)
    assert len(data2) != 2


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/484")
def test004_search_using_two_filters():
    """TC563
    #. Start threebot server, add registery package, then reload the client.
    #. Register user1's data (D1) with adding country_code (C1)
    #. Register user1's data (D2) with adding topic (T1) ans same country code (C1)
    #. Get data using filter C1, should get D1 and D2
    #. Get data using filters T1 and C1, should only get D2
    """

    info("Register user1's data (D1) with adding country_code (C1)")
    x = j.data.idgenerator.generateXCharID(10)
    schema, model = getSchemaAndModel(x)
    author = getNewUser()
    C1 = register_using_filter("country_code", schema=schema, authors=[author.tid], model=model)

    info("Register user1's data (D2) with adding topic (T1) and same country code (C1)")
    x2 = j.data.idgenerator.generateXCharID(10)
    schema, model = getSchemaAndModel(x2)
    T1 = "TRAVEL"
    j.clients.tfgrid_registry.register(schema=schema, authors=[author.tid], model=model, country_code=C1, topic=T1)

    info("Get data using filter C1, should get D1 and D2")
    data = find_using_filter("country_code", C1)
    assert len(data) == 2
    lst = [obj["x"] for obj in data]
    assert x in lst
    assert x2 in lst

    info("Get data using filters T1 and C1, should only get D2")
    res2 = j.clients.tfgrid_registry.find_formatted(registered_info_format="yaml", country_code=C1, topic=T1)
    data2 = j.data.serializers.yaml.loads(res2)
    assert len(data2) != 1
    assert data2[1]["x"] == x2
