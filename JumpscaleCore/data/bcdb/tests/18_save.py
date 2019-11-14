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
from unittest import TestCase


def main(self):
    """
    to run:
    kosmos 'j.data.bcdb.test(name="save")'

    """
    test_case = TestCase()

    scm = """
        @url = test.schema.1
         name** = "" (S)
         number = (I)
         """

    # Scenario 1
    # Saving two objects with different names
    schema = j.data.schema.get_from_text(scm)
    bcdb = j.data.bcdb.get("test")
    model = bcdb.model_get(schema=schema)
    schema_obj = model.new()
    schema_obj.name = "test1"
    schema_obj.number = 10
    schema_obj.save()
    schema_obj2 = model.new()
    schema_obj2.name = "test2"
    schema_obj2.number = 55
    schema_obj2.save()
    assert isinstance(schema_obj.id, int)
    assert isinstance(schema_obj2.id, int)

    # Scenario 2
    # Saving an object with already exist name (Not unique name)
    schema_obj3 = model.new()
    schema_obj3.name = "test2"
    schema_obj3.number = 55
    with test_case.assertRaises(j.exceptions.Input):
        schema_obj3.save()

    # Scenario 3
    # Saving an object with empty name while it has a name in its schema
    schema_obj4 = model.new()
    schema_obj4.number = 55
    with test_case.assertRaises(j.exceptions.Input):
        schema_obj3.save()

    # Scenario 4
    # Update already saved object
    schema_obj2.number = 5500
    schema_obj2.save()
    assert isinstance(schema_obj2.id, int)

    # Scenraio 5
    # Update already saved object with not unique name
    schema_obj2.name = "test1"
    with test_case.assertRaises(j.exceptions.Input):
        schema_obj2.save()
