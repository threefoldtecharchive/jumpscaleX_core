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

# raise j.exceptions.Base("needs to be part of tests on BCDB not here")
bcdb = j.data.bcdb.get("test")


def after():
    bcdb.reset()


def test022_unique_attributes():
    """
    SCM-022
    *Test case for unique attribute *

    **Test Scenario:**

    #. Create schema with unique attributes and save it.
    #. Create another object and try to use same name for first one, should fail.
    #. On the second object, try to use same test var for first one, should fail.
    #. On the second object, try to use same new_name for first one, should success.
    #. On the second object, try to use same number for first one, should fail.
    #. Change name of the first object and try to use the first name again, should success.
    #. Change test var of the first object and try to use the first test var again, should success.
    #. Change number of the first object and try to use the first number again, should success.
    #. Delete the second object and create new one.
    #. Set the new object's attributes with the same attributes of the second object, should success.
    """
    log("Create schema with unique attributes and save it")
    scm = """
    @url = test.schema.1
    name** = "" (S)
    new_name = "" (S)
    &test = "" (S)
    &number = 0 (I)
    """
    schema = j.data.schema.get_from_text(scm)
    model = bcdb.model_get(schema=schema)
    schema_obj = model.new()
    name = random_string()
    new_name = random_string()
    test = random_string()
    number = random.randint(1, 99)
    schema_obj.name = name
    schema_obj.new_name = new_name
    schema_obj.test = test
    schema_obj.number = number
    schema_obj.save()
    import ipdb

    ipdb.set_trace()
    log("Create another object and try to use same name for first one, should fail")
    schema_obj2 = model.new()
    schema_obj2.name = random_string()

    log("On the second object, try to use same test var for first one, should fail")
    schema_obj2.test = test
    try:
        schema_obj2.save()
        raise "error should be raised here"
    except Exception as e:
        log("error raised {}".format(e))
    schema_obj2.test = random_string()

    log("On the second object, try to use same new_name for first one, should success")
    schema_obj2.new_name = new_name
    schema_obj2.save()

    log("On the second object, try to use same number for first one, should fail")
    schema_obj2.number = number
    try:
        schema_obj2.save()
        raise "error should be raised here"
    except Exception as e:
        log("error raised {}".format(e))
    schema_obj2.number = random.randint(100, 199)

    log("Change name of the first object and try to use the first name again, should success")
    schema_obj.name = random_string()
    schema_obj.save()
    schema_obj2.name = name
    schema_obj2.save()

    log("Change test var of the first object and try to use the first test var again, should success")
    schema_obj.test = random_string()
    schema_obj.save()
    schema_obj2.test = test
    schema_obj2.save()

    log("Change number of the first object and try to use the first number again, should success")
    schema_obj.number = random.randint(200, 299)
    schema_obj.save()
    schema_obj2.number = number
    schema_obj2.save()

    log("Delete the second object and create new one.")
    schema_obj2.delete()
    schema_obj3 = model.new()

    log("Set the new object's attributes with the same attributes of the second object, should success.")
    schema_obj3.name = name
    schema_obj3.test = test
    schema_obj3.new_name = new_name
    schema_obj3.number = number
    schema_obj3.save()
