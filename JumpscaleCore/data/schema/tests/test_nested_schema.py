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

import random
import time
from time import sleep
from uuid import uuid4
from datetime import datetime
from Jumpscale import j
from Jumpscale.data.schema.tests.schema import Schema


def log(msg):
    j.core.tools.log(msg, level=20)


def random_string():
    return "s" + str(uuid4()).replace("-", "")[:10]


schema = Schema


def test_001_nested_concatenated_schema():
    """
    SCM-039
    *Test case for concatenated nesting schema *

    **Test Scenario:**

    #. Create three schemas on one schema with different datatypes, should succeed.
    #. Set data to schema parameters, should succeed.
    #. Check that data reflected correctly.
    """
    log("Create three schemas with different datatypes, should succeed.")
    scm3 = """
    @url = student.schema
    name = (S)
    numbers = (O) !phone.schema
    address = (O) !address.schema
    grades = (Lp)



    @url = phone.schema
    mobile_number = "+32475999999"(tel)
    home_number = "+324759999888" (tel)

    @url = address.schema
    country = (S)
    city = (S)
    street = (S)
    building = (I)
    """

    schema3 = schema(scm3)
    schema_obj3 = schema3.new()

    log("Set data to schema parameters, should succeed.")
    name = random_string()
    mobile_number = "{}".format(random.randint(1000000000, 2000000000))
    home_number = "{}".format(random.randint(500000000, 900000000))
    country = random_string()
    city = random_string()
    street = random_string()
    building = random.randint(1, 100)
    grades = [random.randint(0, 1), random.uniform(0, 1)]

    schema_obj3.name = name
    schema_obj3.numbers.mobile_number = mobile_number
    schema_obj3.numbers.home_number = home_number
    schema_obj3.address.country = country
    schema_obj3.address.city = city
    schema_obj3.address.street = street
    schema_obj3.address.building = building
    schema_obj3.grades = grades

    log("Check that data reflected correctly")
    assert schema_obj3.name == name
    assert schema_obj3.numbers.mobile_number == mobile_number
    assert schema_obj3.numbers.home_number == home_number
    assert schema_obj3.address.country == country
    assert schema_obj3.address.city == city
    assert schema_obj3.address.street == street
    assert schema_obj3.address.building == building
    assert schema_obj3.grades == grades


def test_002_nested_sperated_schema():
    """
    SCM-040
    *Test case for sperated nesting schema *

    **Test Scenario:**

    #. Create three schemas on one schema with different datatypes, should succeed.
    #. Set data to schema parameters, should succeed.
    #. Check that data reflected correctly.
    """
    log("Create three schemas with different datatypes, should succeed.")
    scm1 = """
    @url = phone.schema
    mobile_number = "" (tel)
    home_number = "" (tel)
    """
    scm2 = """
    @url = address.schema
    country = (S)
    city = (S)
    street = (S)
    building = (I)
    """
    scm3 = """
    @url = student.schema
    name = (S)
    numbers = (O) !phone.schema
    address = (O) !address.schema
    grades = (Lp)

    """
    schema1 = schema(scm1)
    schema_obj1 = schema1.new()

    schema2 = schema(scm2)
    schema_obj2 = schema2.new()

    schema3 = schema(scm3)
    schema_obj3 = schema3.new()

    log("Set data to schema parameters, should succeed.")
    name = random_string()
    mobile_number = "{}".format(random.randint(1000000000, 2000000000))
    home_number = "{}".format(random.randint(500000000, 900000000))
    country = random_string()
    city = random_string()
    street = random_string()
    building = random.randint(1, 100)
    grades = [random.randint(0, 1), random.randint(0, 1)]

    schema_obj3.name = name
    schema_obj3.numbers.mobile_number = mobile_number
    schema_obj3.numbers.home_number = home_number
    schema_obj3.address.country = country
    schema_obj3.address.city = city
    schema_obj3.address.street = street
    schema_obj3.address.building = building
    schema_obj3.grades = grades

    log("Check that data reflected correctly")
    assert schema_obj3.name == name
    assert schema_obj3.numbers.mobile_number == mobile_number
    assert schema_obj3.numbers.home_number, home_number
    assert schema_obj3.address.country == country
    assert schema_obj3.address.city == city
    assert schema_obj3.address.street == street
    assert schema_obj3.address.building == building
    assert schema_obj3.grades == grades
