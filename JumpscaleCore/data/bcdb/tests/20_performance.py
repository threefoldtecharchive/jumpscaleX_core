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


def test_performance():
    """
    to run:

    kosmos 'j.data.bcdb.test(name="performance")'

    """

    def calculate_write_time(model):
        j.tools.timer.start()
        for _ in range(1000):
            obj = model.new()
            text = j.data.idgenerator.generateXCharID(64)
            obj.text = text
            obj.save()
        j.tools.timer.stop(nritems=1000)

    def calculate_read_time(model):
        j.tools.timer.start()
        for _ in range(1000):
            text = j.data.idgenerator.generateXCharID(64)
            model.find(text=text)
        j.tools.timer.stop(nritems=1000)

    def sonic_query(model):
        j.tools.timer.start()
        for _ in range(1000):
            text = j.data.idgenerator.generateXCharID(64)
            model.search(text=text)
        j.tools.timer.stop(nritems=1000)

    def test_write_read(type="zdb"):
        schema = """
        @url = test.text.1
        text = "" (S)

        @url = test.index.1
        text** = (S)
        """
        bcdb, _ = j.data.bcdb._test_model_get(type=type, schema=schema)
        string_model = bcdb.model_get(url="test.text.1")
        indexed_model = bcdb.model_get(url="test.index.1")

        print(f"\nWrite objects of 64 Bytes of string ({type} backend)")
        calculate_write_time(string_model)

        print(f"\nWrite indexed objects of 64 Bytes of string ({type} backend)")
        calculate_write_time(indexed_model)

        # Query time should be the same for all backend
        print(f"\nQuery objects ({type} backend)")
        calculate_read_time(indexed_model)

        bcdb.reset()

    test_write_read(type="zdb")
    test_write_read(type="rdb")
    test_write_read(type="sqlite")

    schema = """
    @url = test.sonic.1
    text*** = (S)
    """
    bcdb, model = j.data.bcdb._test_model_get(schema=schema)

    print("\nWrite objects of 64 Bytes of string (sonic)")
    calculate_write_time(model)

    print("\nQuery in sonic")
    sonic_query(model)
    bcdb.reset()


# Teardown
def after():
    # Destroy rdb,sqlite and zdb databases
    j.data.bcdb.test_rdb.destroy()
    j.data.bcdb.test_sqlite.destroy()
    j.data.bcdb.test_zdb.destroy()
    # Stop and delete sonic
    j.servers.sonic.testserver.stop()
    j.servers.sonic.testserver.delete()
    # Stop and delete zdb
    j.servers.zdb.testserver.stop()
    j.servers.zdb.testserver.delete()

