from Jumpscale import j

####

# To Be reviewed in jumpscale 10.3

###

skip = j.baseclasses.testtools._skip


def test_export():
    """
    to run:
    kosmos 'j.data.bcdb.test(name="export")'

    """

    namespaces = ["testexport_zdb", "testexport_sqlite"]

    schema_text = """
    @url = farm.1
    name** = (S)
    threebot_id = "default"
    iyo_organization = "default"
    resource_prices = (LO) !node.resource.price.1

    @url = node.resource.price.1
    currency = "EUR,USD,TFT,AED,GBP" (E)
    cru = (F)
    mru = (F)
    hru = (F)
    sru = (F)
    nru = (F)
    """
    schema_text2 = """
    @url = node.1
    size = (I)
    """
    schema = j.data.schema.get_from_text(schema_text)
    schema2 = j.data.schema.get_from_text(schema_text2)

    def export_import(bcdb, farm_model, node_model, export_folder_name="export_test", encrypt=False):
        j.data.bcdb.export(path=f"/tmp/bcdb_export/{export_folder_name}", encrypt=encrypt)
        assert len(farm_model.find()) == 10
        assert len(node_model.find()) == 8
        j.data.bcdb.import_(
            path=f"/tmp/bcdb_export/{export_folder_name}", interactive=False, reset=False, is_test_env=True
        )
        assert len(farm_model.find()) == 10
        assert len(node_model.find()) == 8

    # Testing using ZDB storeclient
    bcdb_zdb, farm_model_zdb, node_model_zdb = load(name="zdb", schema=schema_text, schema2=schema2)
    export_import(bcdb_zdb, farm_model_zdb, node_model_zdb, export_folder_name="zdb_with_encry", encrypt=False)
    # encryption is not implemented yet
    # export_import(bcdb_zdb, farm_model_zdb, node_model_zdb, export_folder_name="zdb_without_encry", encrypt=True)

    # Testing using SQl storeclient
    bcdb_sql, farm_model_sql, node_model_sql = load(name="sqlite", schema=schema_text, schema2=schema2)
    export_import(bcdb_sql, farm_model_sql, node_model_sql, export_folder_name="sql_with_encry", encrypt=False)
    # encryption is not implemented yet
    # export_import(bcdb_sql, farm_model_sql, node_model_sql, export_folder_name="sql_without_encry", encrypt=True)

    j.data.bcdb._log_info("TEST DONE")
    return "OK"


def load(name, schema, schema2):
    bcdb, farm_model = j.data.bcdb._test_model_get(type=name, schema=schema)
    # bcdb.reset()
    for i in range(10):
        farm = farm_model.new()
        farm.threebot_id = i
        farm.iyo_organization = str(i)
        farm.name = str(i)
        farm.save()

    node_model = bcdb.model_get(schema2)

    for i in range(10):
        node = node_model.new()
        node.size = i
        node.save()

    node_model.find()[0].delete()
    node_model.find()[0].delete()
    return bcdb, farm_model, node_model


# Teardown
def after():
    # Destroy sqlite and zdb databases
    j.data.bcdb.test_sqlite.destroy()
    j.data.bcdb.test_zdb.destroy()
    j.data.bcdb.system.destroy()
    # Stop and delete sonic
    j.servers.sonic.testserver.stop()
    j.servers.sonic.testserver.delete()
    # Stop and delete zdb
    j.servers.zdb.testserver.stop()
    j.servers.zdb.testserver.delete()

