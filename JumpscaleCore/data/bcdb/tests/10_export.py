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

    j.servers.zdb.test_instance_start()

    SCHEMA = """
    @url = threefoldtoken.wallet.test
    name* = "wallet"
    addr = ""                   # Address
    ipaddr = (ipaddr)           # IP Address
    email = "" (S)              # Email address
    username = "" (S)           # User name
    
    """
    bcdb = j.data.bcdb.new("test_export", reset=True)

    m = bcdb.model_get(schema=SCHEMA)
    # model ID will go from 1 to 10
    for i in range(10):
        o = m.new()
        assert o._model.schema.url == "threefoldtoken.wallet.test"
        o.addr = "something:%s" % i
        o.email = "myemail"
        o.name = "myuser_%s" % i
        o.save()

    SCHEMA2 = """
    @url = threefoldtoken.wallet.test2
    lastname* = "lienard"
    firstname = ""                   # Address    
    """

    m2 = bcdb.model_get(schema=SCHEMA2)
    # model ID will go from 11 to 20
    for i in range(10):
        o = m2.new()
        assert o._model.schema.url == "threefoldtoken.wallet.test2"
        o.firstname = "firstname:%s" % i
        o.lastname = "lastname:%s" % i
        o.save()

    p = "/tmp/bcdb_export"

    def export_import(encr=False, export=True, remove=False):
        if export:
            j.sal.fs.remove(p)
            bcdb.export(path=p, encrypt=encr)

        obj = m2.get(13)  # because we check the second model that starts with id 11
        bcdb.reset()

        try:
            m2.get(13)
            raise j.exceptions.Base("should not exist")
        except:
            pass

        bcdb.import_(path=p)
        m3 = bcdb.model_get(schema=SCHEMA2)

        obj2 = m3.get(13)

        assert obj2._ddict_hr == obj._ddict_hr
        # data contains schema ID which should be the same as import export is ID deterministic
        assert obj2._ddict_json_hr == obj._ddict_json_hr

        assert obj._schema == obj2._schema

        if remove:
            j.sal.fs.remove(p)

    export_import(encr=False, export=True, remove=False)
    # will now test if we can import
    export_import(False, export=False, remove=True)
    # now do other test because there will be stuff changed
    export_import(encr=False, export=True, remove=True)

    # now test with encryption
    export_import(encr=True, export=True, remove=False)
    export_import(encr=True, export=False, remove=True)

    self._log_info("TEST DONE")
    return "OK"
