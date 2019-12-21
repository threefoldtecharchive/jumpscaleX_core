from Jumpscale import j

####

# To Be reviewed in jumpscale 10.3

###


def main(self):
    """
    to run:
    kosmos 'j.data.bcdb.test(name="export")'

    """
    return

    zdb = j.servers.zdb.test_instance_start()

    namespaces = ["testexport_zdb", "testexport_sqlite"]

    def cleanup():
        for namespace in namespaces:
            if namespace in j.data.bcdb.instances:
                bcdb = j.data.bcdb.instances[namespace]
                bcdb.destroy()

    cleanup()

    schema_text = """
    @url = farm.1
    name** = (S)
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

    for namespace in namespaces:
        if namespace == "testexport_zdb":
            adminsecret_ = j.data.hash.md5_string(zdb.adminsecret_)
            zdb_admin = zdb.client_admin_get()

            if not zdb_admin.namespace_exists(namespace):
                zdb_admin.namespace_new(namespace, secret=adminsecret_, maxsize=0, die=True)
            storclient = zdb.client_get(namespace, adminsecret_)
            bcdb = j.data.bcdb.get(name=namespace, storclient=storclient)
        else:
            bcdb = j.data.bcdb.get(name=namespace)

        farm_model = bcdb.model_get(schema)

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

    def export_import(encrypt=False):
        for namespace in namespaces:
            bcdb = j.data.bcdb.get(name=namespace)
            farm_model = bcdb.model_get(schema)
            node_model = bcdb.model_get(schema2)

            bcdb.export(f"/tmp/bcdb_export/{namespace}", encrypt=encrypt)

            assert len(farm_model.find()) == 10
            assert len(node_model.find()) == 8

            bcdb.reset()
            assert bcdb.storclient.count == 1
            bcdb.import_(f"/tmp/bcdb_export/{namespace}", interactive=False)

            assert len(farm_model.find()) == 10
            assert len(node_model.find()) == 8

    export_import(encrypt=True)
    export_import(encrypt=False)
    cleanup()
    j.servers.zdb.test_instance_stop()
    self._log_info("TEST DONE")
    return "OK"
