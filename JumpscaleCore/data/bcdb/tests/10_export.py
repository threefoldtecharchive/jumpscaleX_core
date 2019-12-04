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
    kosmos 'j.data.bcdb.test(name="export")'

    """
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

    zdb = j.servers.zdb.test_instance_start()

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
        node_model = bcdb.model_get(schema2)

        for i in range(10):
            farm = farm_model.new()
            farm.threebot_id = i
            farm.iyo_organization = str(i)
            farm.name = str(i)
            farm.save()

        farm_model.find()[0].delete()
        farm_model.find()[0].delete()

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

            assert len(farm_model.find()) == 8
            assert len(node_model.find()) == 8

            bcdb.reset()
            assert bcdb.storclient.count == 1

            bcdb.import_(f"/tmp/bcdb_export/{namespace}", interactive=False)

            assert len(farm_model.find()) == 8
            assert len(node_model.find()) == 8

    export_import(encrypt=False)
    export_import(encrypt=True)

    cleanup()

    self._log_info("TEST DONE")
    return "OK"
