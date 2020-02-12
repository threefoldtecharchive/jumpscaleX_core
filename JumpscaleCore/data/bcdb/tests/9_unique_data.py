from Jumpscale import j
import random
from uuid import uuid4

from unittest import TestCase


def test_unique_data():
    """
    to run:

    kosmos 'j.data.bcdb.test(name="unique_data")'

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

    j.core.tools.log("Create schema with unique attributes and save it", level=20)
    test_case = TestCase()
    scm = """
    @url = test.schema.1
    &name** = "" (S)
    new_name = "" (S)
    &test = "" (S)
    &number = 0 (I)
    """

    bcdb, model = j.data.bcdb._load_test_model(type="zdb", schema=scm)

    schema_obj = model.new()
    name = "s" + str(uuid4()).replace("-", "")[:10]
    new_name = "s" + str(uuid4()).replace("-", "")[:10]
    test = "s" + str(uuid4()).replace("-", "")[:10]
    number = random.randint(1, 99)

    schema_obj.name = name
    schema_obj.new_name = new_name
    schema_obj.test = test
    schema_obj.number = number
    schema_obj.save()

    j.core.tools.log("Create another object and try to use same name for first one, should fail", level=20)
    schema_obj2 = model.new()
    schema_obj2.name = schema_obj.name

    with test_case.assertRaises(Exception):
        schema_obj2.save()

    j.core.tools.log("On the second object, try to use same test var for first one, should fail", level=20)
    schema_obj2.name = "s" + str(uuid4()).replace("-", "")[:10]
    schema_obj2.test = test
    with test_case.assertRaises(Exception):
        schema_obj2.save()

    j.core.tools.log("On the second object, try to use same new_name for first one, should success", level=20)
    schema_obj2.test = "s" + str(uuid4()).replace("-", "")[:10]
    schema_obj2.new_name = new_name
    schema_obj2.save()

    j.core.tools.log("On the second object, try to use same number for first one, should fail", level=20)
    schema_obj2.number = number
    with test_case.assertRaises(Exception):
        schema_obj2.save()
    # check that in DB only 1 matches from the past
    r4 = model.find(name=schema_obj.name)
    print(r4)

    assert r4[0].id == schema_obj.id

    assert len(r4) == 1  # there should be one in DB and index should return 1

    j.core.tools.log("Change name of the first object and try to use the first name again, should success", level=20)
    schema_obj.name = "s" + str(uuid4()).replace("-", "")[:10]
    schema_obj.save()
    schema_obj2.number = random.randint(200, 299)
    schema_obj2.name = name
    schema_obj2.save()

    j.core.tools.log(
        "Change test var of the first object and try to use the first test var again, should success", level=20
    )
    schema_obj.test = "s" + str(uuid4()).replace("-", "")[:10]
    schema_obj.save()
    schema_obj2.test = test
    schema_obj2.save()

    j.core.tools.log(
        "Change number of the first object and try to use the first number again, should success", level=20
    )
    schema_obj.number = random.randint(100, 199)
    schema_obj.save()
    schema_obj2.test = number
    schema_obj2.save()

    j.core.tools.log("Delete the second object and create new one.", level=20)
    name = schema_obj2.name + ""
    test = schema_obj2.test + ""
    number = schema_obj2.number + 0
    args_search = {"name": name}
    r = model.find(**args_search)
    assert len(r) == 1
    schema_obj2.delete()
    with test_case.assertRaises(Exception) as cm:
        model.get(schema_obj2.id)
    ex = cm.exception
    assert "not find obj with id:%s" % schema_obj2.id in str(ex.args[0])

    # lets now check that the index has been cleaned
    args_search = {"name": name}
    r = model.find(**args_search)
    assert len(r) == 0

    try:
        schema_obj2.save()
    except:
        assert Exception

    j.core.tools.log(
        "Set the new object's attributes with the same attributes of the second object, should success.", level=20
    )
    schema_obj3 = model.new()
    assert schema_obj3.id is None
    schema_obj3.name = schema_obj2.name
    schema_obj3.new_name = schema_obj2.new_name
    schema_obj3.test = schema_obj2.test
    schema_obj3.number = schema_obj2.number
    schema_obj3.save()
