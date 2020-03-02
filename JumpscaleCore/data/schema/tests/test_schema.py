import random
import time
from time import sleep
from uuid import uuid4
from datetime import datetime
from Jumpscale import j
from Jumpscale.data.schema.tests.schema import Schema
import unittest


def log(msg):
    j.core.tools.log(msg, level=20)


def random_string():
    return "s" + str(uuid4()).replace("-", "")[:10]


def almost_equal(value_1, value_2, delta):
    return abs(value_1 - value_2) < delta


T = unittest.TestCase()
schema = Schema


def test001_validate_string_type():
    """
    SCM-001
    *Test case for validating string type *

    **Test Scenario:**

    #. Create schema with string parameter[P1], should succeed.
    #. Try to set parameter[P1] with string type, should succeed.
    """
    log("Create schema with string parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    name = (S)
    init_str_1 = "test string 1" (S)
    init_str_2 = 'test string 2' (S)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with string type, should succeed.")
    name = random_string()
    schema_obj.name = name
    assert schema_obj.name == name
    assert schema_obj.init_str_1 == "test string 1"
    assert schema_obj.init_str_2 == "test string 2"


def test_002_validate_integer_type():
    """
    SCM-002
    *Test case for validating integer type *

    **Test Scenario:**

    #. Create schema with integer parameter[P1], should succeed.  #TODO: NOT TRUE, we convert types to the base type if possible !
    #. Try to set parameter[P1] with non integer type, should fail.
    #. Try to set parameter[P1] with integer type, should succeed.
    """
    log("Create schema with integer parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    number = (I)
    init_int = 123 (I)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with type which cannot convert to integer should fail.")
    with T.assertRaises(Exception):
        schema_obj.number = random_string()

    with T.assertRaises(Exception):
        schema_obj.number = [random.randint(1, 1000), random.randint(1, 1000)]

    log("Try to set parameter[P1] with integer type, should succeed.")
    rand_num = random.randint(1, 1000)
    schema_obj.number = rand_num
    assert schema_obj.number == rand_num
    assert schema_obj.init_int == 123


def test_003_validate_float_type():
    """
    SCM-003
    *Test case for validating float type *

    **Test Scenario:**

    #. Create schema with float parameter[P1], should succeed.
    #. Try to set parameter[P1] with non float type, should fail.
    #. Try to set parameter[P1] with float type, should succeed.
    """
    log("Create schema with float parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    number = (F)
    init_float = 84.32 (F)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non float type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.number = random_string()

    with T.assertRaises(Exception):
        schema_obj.number = [random.uniform(10, 20), random.uniform(10, 20)]

    with T.assertRaises(Exception):
        schema_obj.number = {"number": random.uniform(10, 20)}

    log("Try to set parameter[P1] with float type, should succeed.")
    rand_num = random.uniform(10, 20)
    schema_obj.number = rand_num
    assert schema_obj.number == rand_num
    assert schema_obj.init_float == 84.32


def test_004_validate_boolean_type():
    """
    SCM-004
    *Test case for validating boolean type *

    **Test Scenario:**

    #. Create schema with boolean parameter[P1], should succeed.
    #. Try to set parameter[P1] with False or non True value, should be False.
    #. Try to set parameter[P1] with True value, should be True.
    """
    log("Create schema with boolean parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    check = (B)
    init_bool_1 = 'y' (B)
    init_bool_2 = 1 (B)
    init_bool_3 = 'yes' (B)
    init_bool_4 = 'true' (B)
    init_bool_5 = True (B)
    init_bool_6 = 'n' (B)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with False or non True value, should be False.")
    schema_obj.check = False
    assert schema_obj.check == False

    schema_obj.check = random.randint(10, 20)
    assert schema_obj.check is False

    schema_obj.check = random.uniform(10, 20)
    assert schema_obj.check is False

    schema_obj.check = random_string()
    assert schema_obj.check is False

    schema_obj.check = [True, False]
    assert schema_obj.check == False

    schema_obj.check = {"number": True}
    assert schema_obj.check == False
    assert schema_obj.init_bool_6 == False

    log("Try to set parameter[P1] with True value, should be True.")
    schema_obj.check = True
    assert schema_obj.check is True

    schema_obj.check = 1
    assert schema_obj.check is True

    schema_obj.check = "1"
    assert schema_obj.check is True

    schema_obj.check = "yes"
    assert schema_obj.check is True

    schema_obj.check = "y"
    assert schema_obj.check is True

    schema_obj.check = "true"
    assert schema_obj.check is True
    assert schema_obj.init_bool_1 == True
    assert schema_obj.init_bool_2 == True
    assert schema_obj.init_bool_3 == True
    assert schema_obj.init_bool_4 == True
    assert schema_obj.init_bool_5 == True


def test_005_validate_mobile_type():
    """
    SCM-005
    *Test case for validating mobile type *

    **Test Scenario:**

    #. Create schema with mobile parameter[P1], should succeed.
    #. Try to set parameter[P1] with non mobile type, should fail.
    #. Try to set parameter[P1] with mobile type, should succeed.
    """
    log("Create schema with mobile parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    mobile = (tel)
    init_tel_1 = '464-4564-464' (tel)
    init_tel_2 = '+45687941' (tel)
    init_tel_3 = 468716420 (tel)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non mobile type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.mobile = random_string()

    with T.assertRaises(Exception):
        schema_obj.mobile = random.randint(10, 20)

    with T.assertRaises(Exception):
        schema_obj.mobile = random.uniform(10, 20)

    with T.assertRaises(Exception):
        schema_obj.mobile = [
            "{}".format(random.randint(100000, 1000000)),
            "{}".format(random.randint(100000, 1000000)),
        ]
    with T.assertRaises(Exception):
        schema_obj.mobile = {"number": "{}".format(random.randint(100000, 1000000))}

    log("Try to set parameter[P1] with mobile type, should succeed.")
    number = "{}".format(random.randint(100000, 1000000))
    schema_obj.mobile = number
    assert schema_obj.mobile == number

    number = "+{}".format(random.randint(100000, 1000000))
    schema_obj.mobile = number
    assert schema_obj.mobile == number

    schema_obj.mobile = "464-4564-464"
    assert schema_obj.mobile == "4644564464"
    assert schema_obj.init_tel_1 == "4644564464"
    assert schema_obj.init_tel_2 == "+45687941"
    assert schema_obj.init_tel_3 == "468716420"


def test_006_validate_email_type():
    """
    SCM-006
    *Test case for validating email type *

    **Test Scenario:**

    #. Create schema with email parameter[P1], should succeed.
    #. Try to set parameter[P1] with non email type, should fail.
    #. Try to set parameter[P1] with email type, should succeed.
    """
    log("Create schema with email parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    email = (email)
    init_email_1 = "test.example@domain.com" (email)
    init_email_2 = test.example@domain.com (email)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non email type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.email = random.randint(1, 100)

    with T.assertRaises(Exception):
        schema_obj.email = random.uniform(1, 100)

    with T.assertRaises(Exception):
        schema_obj.email = random_string()

    with T.assertRaises(Exception):
        schema_obj.email = "example.com"

    with T.assertRaises(Exception):
        schema_obj.email = "example@com"

    with T.assertRaises(Exception):
        schema_obj.email = ["test.example@domain.com", "test.example@domain.com"]

    with T.assertRaises(Exception):
        schema_obj.email = {"number": "test.example@domain.com"}

    log("Try to set parameter[P1] with email type, should succeed.")
    schema_obj.email = "test.example@domain.com"
    assert schema_obj.email == "test.example@domain.com"
    assert schema_obj.init_email_1 == "test.example@domain.com"
    assert schema_obj.init_email_2 == "test.example@domain.com"


def test_007_validate_ipport_type():
    """
    SCM-007
    *Test case for validating ipport type *

    **Test Scenario:**

    #. Create schema with ipport parameter[P1], should succeed.
    #. Try to set parameter[P1] with non ipport type, should fail.
    #. Try to set parameter[P1] with ipport type, should succeed.
    """
    log("Create schema with ipport parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    port = (ipport)
    init_port = 12315 (ipport)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non ipport type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.port = random.randint(10000000, 100000000)

    with T.assertRaises(Exception):
        schema_obj.port = random_string()

    with T.assertRaises(Exception):
        schema_obj.port = [random.randint(1, 10000), random.randint(1, 10000)]

    with T.assertRaises(Exception):
        schema_obj.port = {"port": random.randint(1, 10000)}
    log("Try to set parameter[P1] with ipport type, should succeed.")
    port = random.randint(1, 10000)
    schema_obj.port = port
    assert schema_obj.port == port
    assert schema_obj.init_port == 12315


def test_008_validate_ipaddr_type():
    """
    SCM-008
    *Test case for validating ipaddr type *

    **Test Scenario:**

    #. Create schema with ipaddr parameter[P1], should succeed.
    #. Try to set parameter[P1] with non ipaddr type, should fail.
    #. Try to set parameter[P1] with ipaddr type, should succeed.
    """
    log("Create schema with ipaddr parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    ip = (ipaddr)
    init_ip_1 = '127.0.0.1' (ipaddr)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non ipaddr type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.ip = random.uniform(1, 100)

    with T.assertRaises(Exception):
        schema_obj.ip = random_string()

    with T.assertRaises(Exception):
        schema_obj.ip = "10.20.256.1"

    with T.assertRaises(Exception):
        schema_obj.ip = "10.20.1"

    with T.assertRaises(Exception):
        schema_obj.ip = [random.randint(0, 255), random.randint(0, 255)]

    with T.assertRaises(Exception):
        schema_obj.ip = {"number": random.randint(0, 255)}

    log("Try to set parameter[P1] with ipaddr type, should succeed.")
    ip = "10.15.{}.1".format(random.randint(0, 255))
    schema_obj.ip = ip
    assert schema_obj.ip == ip
    assert schema_obj.init_ip_1 == "127.0.0.1"


def test_009_validate_iprange_type():
    """
    SCM-009
    *Test case for validating iprange type *

    **Test Scenario:**

    #. Create schema with iprange parameter[P1], should succeed.
    #. Try to set parameter[P1] with non iprange type, should fail.
    #. Try to set parameter[P1] with iprange type, should succeed.
    """
    log("Create schema with iprange parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    iprange = (iprange)
    init_iprange = '127.0.0.1/16' (iprange)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non iprange type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.iprange = random.uniform(1, 100)

    with T.assertRaises(Exception):
        schema_obj.iprange = random_string()

    with T.assertRaises(Exception):
        schema_obj.iprange = "10.20.256.1"

    with T.assertRaises(Exception):
        schema_obj.iprange = "10.20.1"

    with T.assertRaises(Exception):
        schema_obj.iprange = "10.20.1.0/"

    with T.assertRaises(Exception):
        schema_obj.iprange = [random.randint(1, 100), random.randint(1, 100)]

    with T.assertRaises(Exception):
        schema_obj.iprange = {"number": random.randint(1, 100)}
    log("Try to set parameter[P1] with iprange type, should succeed.")
    iprange = random.randint(1, 100)
    schema_obj.iprange = iprange
    assert schema_obj.iprange == iprange

    iprange = "10.20.1.0"
    schema_obj.iprange = iprange
    assert schema_obj.iprange == iprange

    iprange = "10.15.{}.1/24".format(random.randint(0, 255))
    schema_obj.iprange = iprange
    assert schema_obj.iprange == iprange
    assert schema_obj.init_iprange == "127.0.0.1/16"


def test_010_validate_date_type():
    """
    SCM-010
    *Test case for validating date type *

    **Test Scenario:**

    #. Create schema with date parameter[P1], should succeed.
    #. Try to set parameter[P1] with non date type, should fail.
    #. Try to set parameter[P1] with date type, should succeed.
    """
    log("Create schema with date parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    date_time = (t)
    date = (d)
    init_date_time = 01/01/2019 9pm:10 (t)
    init_date = 05/03/1994 (d)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non date type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.date_time = random.uniform(1, 100)

    with T.assertRaises(Exception):
        schema_obj.date_time = random_string()

    with T.assertRaises(Exception):
        date_time = "{:02}/31".format(random.choice([2, 4, 6, 9, 11]))
        schema_obj.date_time = date_time

    with T.assertRaises(Exception):
        date_time = "2014/02/29"
        schema_obj.date = date_time

    with T.assertRaises(Exception):
        date_time = "201/02/29"
        schema_obj.date_time = date_time

    with T.assertRaises(Exception):
        date_time = "2014/02/01 {}{}:12".format(random.choice(random.randint(13, 23), 0), random.choice("am", "pm"))
        schema_obj.date_time = date_time

    with T.assertRaises(Exception):
        schema_obj.date_time = [random.randint(1, 9), random.randint(1, 9)]

    with T.assertRaises(Exception):
        schema_obj.date_time = {"date": random.randint(1, 9)}
    log("Try to set parameter[P1] with date type, should succeed.")
    date_time = 0
    schema_obj.date_time = date_time
    assert schema_obj.date_time == date_time

    date_time = random.randint(1, 200)
    schema_obj.date_time = date_time
    assert schema_obj.date_time == date_time

    year = random.randint(1000, 2020)
    year_2c = random.randint(1, 99)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    hour = random.randint(0, 23)
    hour_12 = random.randint(1, 11)
    minutes = random.randint(0, 59)
    am_or_pm = random.choice(["am", "pm"])
    hours = hour_12 if am_or_pm == "am" else hour_12 + 12
    years = 1900 if year_2c >= 69 else 2000

    date = datetime(year, month, day).timestamp()
    schema_obj.date = "{}/{:02}/{:02}".format(year, month, day)
    assert schema_obj.date == int(date)

    date_time = datetime(datetime.now().year, month, day).timestamp()
    schema_obj.date_time = "{:02}/{:02}".format(month, day)
    assert schema_obj.date_time == int(date_time)

    date_time = datetime(datetime.now().year, month, day, hour, minutes).timestamp()
    schema_obj.date_time = "{:02}/{:02} {:02}:{:02}".format(month, day, hour, minutes)
    assert schema_obj.date_time == int(date_time)

    date_time = datetime(year, month, day).timestamp()
    schema_obj.date_time = "{}/{:02}/{:02}".format(year, month, day)
    assert schema_obj.date_time == int(date_time)

    date_time = datetime(2016, 2, 29).timestamp()
    schema_obj.date_time = "2016/02/29"
    assert schema_obj.date_time == int(date_time)

    date_time = datetime(year, month, day, hour, minutes).timestamp()
    schema_obj.date_time = "{}/{:02}/{:02} {:02}:{:02}".format(year, month, day, hour, minutes)
    assert schema_obj.date_time == int(date_time)

    date_time = datetime((year_2c + years), month, day).timestamp()
    schema_obj.date_time = "{:02}/{:02}/{:02}".format(year_2c, month, day)
    assert schema_obj.date_time == int(date_time)

    date_time = datetime((year_2c + years), month, day, hour, minutes).timestamp()
    schema_obj.date_time = "{:02}/{:02}/{:02} {:02}:{:02}".format(year_2c, month, day, hour, minutes)
    assert schema_obj.date_time == int(date_time)

    date_time = datetime(year, month, day, hours, minutes).timestamp()
    schema_obj.date_time = "{}/{:02}/{:02} {:02}{}:{:02}".format(year, month, day, hour_12, am_or_pm, minutes)
    assert schema_obj.date_time == int(date_time)

    date_time = datetime(year, month, day).timestamp()
    schema_obj.date_time = "{:02}/{:02}/{}".format(day, month, year)
    assert schema_obj.date_time == int(date_time)


def test_011_validate_percent_type():
    """
    SCM-011
    *Test case for validating percent type *

    **Test Scenario:**

    #. Create schema with percent parameter[P1], should succeed.
    #. Try to set parameter[P1] with non percent type, should fail.
    #. Try to set parameter[P1] with percent type, should succeed.
    """
    log("Create schema with percent parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    percent = (percent)
    init_percent_1 = 0 (percent)
    init_percent_2 = 1 (percent)
    init_percent_3 = 0.95 (percent)
    init_percent_4 = 1% (percent)
    init_percent_5 = 0.54% (percent)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non percent type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.percent = random_string()

    with T.assertRaises(Exception):
        schema_obj.percent = "10$"

    with T.assertRaises(Exception):
        schema_obj.percent = ["10", "20"]

    with T.assertRaises(Exception):
        schema_obj.percent = [random.randint(1, 100), random.randint(1, 100)]

    with T.assertRaises(Exception):
        schema_obj.percent = {"number": random.randint(1, 100)}

    log("Try to set parameter[P1] with percent type, should succeed.")
    percent = random.randint(0, 1)
    schema_obj.percent = percent
    assert schema_obj.percent == percent

    percent = random.uniform(0, 1)
    schema_obj.percent = percent
    assert schema_obj.percent == percent

    value = random.randint(0, 1)
    percent = "{}".format(value)
    schema_obj.percent = percent
    assert schema_obj.percent == value

    percent = "{}%".format(value)
    schema_obj.percent = percent
    assert schema_obj.percent == value / 100

    value = random.uniform(0, 1)
    percent = "{}".format(value)
    schema_obj.percent = percent
    assert schema_obj.percent == value

    percent = "{}%".format(value)
    schema_obj.percent = percent
    assert schema_obj.percent == value / 100
    assert schema_obj.init_percent_1 == 0
    assert schema_obj.init_percent_2 == 1
    assert schema_obj.init_percent_3 == 0.95
    assert schema_obj.init_percent_4 == 0.01
    assert schema_obj.init_percent_5 == 0.0054


def test_012_validate_url_type():
    """
    SCM-012
    *Test case for validating url type *

    **Test Scenario:**

    #. Create schema with url parameter[P1], should succeed.
    #. Try to set parameter[P1] with non url type, should fail.
    #. Try to set parameter[P1] with url type, should succeed.
    """
    log("Create schema with url parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    site = (u)
    init_url = 'test.example.com/home' (u)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non url type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.site = random.randint(1, 100)

    with T.assertRaises(Exception):
        schema_obj.site = random.uniform(1, 100)

    with T.assertRaises(Exception):
        schema_obj.site = random_string()

    with T.assertRaises(Exception):
        schema_obj.site = "example@com"

    with T.assertRaises(Exception):
        schema_obj.site = "test/example.com"

    with T.assertRaises(Exception):
        schema_obj.site = [random.randint(1, 100), random.randint(1, 100)]

    with T.assertRaises(Exception):
        schema_obj.site = {"number": random.randint(1, 100)}
    log("Try to set parameter[P1] with url type, should succeed.")
    schema_obj.site = "test.example.com"
    assert schema_obj.site == "test.example.com"

    schema_obj.site = "test.example.com/home"
    assert schema_obj.site == "test.example.com/home"
    assert schema_obj.init_url == "test.example.com/home"


def test_013_validate_numeric_type():
    """
    SCM-013
    *Test case for validating numeric type *

    **Test Scenario:**

    #. Create schema with numeric parameter[P1], should succeed.
    #. Try to set parameter[P1] with non numeric type, should fail.
    #. Try to set parameter[P1] with numeric type, should succeed.
    """
    log("Create schema with numeric parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    number = (N)
    currency = (N)
    init_numeric_1 = '10 usd' (N)
    init_numeric_2 = 10 (N)
    init_numeric_3 = 10.54 (N)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non numeric type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.currency = random_string()

    with T.assertRaises(Exception):
        schema_obj.currency = [random.randint(1, 100), random.randint(1, 100)]

    with T.assertRaises(Exception):
        schema_obj.currency = {"number": random.randint(1, 100)}
    log("Try to set parameter[P1] with numeric type, should succeed.")
    number = random.randint(1, 1000)
    schema_obj.number = number
    assert schema_obj.number_usd == number

    number = random.uniform(1, 1000)
    schema_obj.number = number
    assert schema_obj.number_usd == number

    value = random.randint(1, 100)
    currency = "{} USD".format(value)
    schema_obj.currency = currency
    assert schema_obj.currency_usd == value
    assert schema_obj.init_numeric_1_usd == 10
    assert schema_obj.init_numeric_2_usd == 10
    assert schema_obj.init_numeric_3_usd == 10.54


def test_014_validate_currency_conversion():
    """
    SCM-014
    *Test case for validating currencies conversion *

    **Test Scenario:**

    #. Create schema with numeric parameter[P1], should succeed.
    #. Put one of currencies and convert it to the other currencies and Check result is same as calculated.
    """
    log("Create schema with numeric parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    currency = (N)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Put one of currencies and convert it to the other currencies and Check result is same as calculated")
    currencies = j.clients.currencylayer.cur2usd
    for curr1 in currencies:
        value = random.uniform(1, 100)
        currency = "{} {}".format(value, curr1)
        schema_obj.currency = currency
        for curr2 in currencies:
            assert (
                almost_equal(schema_obj.currency_cur(curr2), value * currencies[curr2] / currencies[curr1], 0.0001)
                is True
            )


def test_015_validate_guid_type():
    """
    SCM-015
    *Test caste for validating guid type *

    **Test Scenario:**

    #. Create schema with guid parameter[P1], should succeed.
    #. Try to set parameter[P1] with non guid type, should fail.
    #. Try to set parameter[P1] with guid type, should succeed.
    """
    log("Create schema with guid parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    guid = (guid)
    init_guid_1 = bebe8b34-b12e-4fda-b00c-99979452b7bd (guid)
    init_guid_2 = 84b022bd-2b00-4b62-8539-4ec07887bbe4 (guid)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non guid type, should fail.")

    with T.assertRaises(Exception):
        schema_obj.guid = random_string()

    with T.assertRaises(Exception):
        schema_obj.guid = str(uuid4())[:15]

    with T.assertRaises(Exception):
        schema_obj.guid = random.randint(1, 1000)

    with T.assertRaises(Exception):
        schema_obj.guid = random.uniform(1, 1000)

    with T.assertRaises(Exception):
        schema_obj.guid = [random.randint(1, 100), random.randint(1, 100)]

    with T.assertRaises(Exception):
        schema_obj.guid = {"number": random.randint(1, 100)}

    log("Try to set parameter[P1] with guid type, should succeed.")
    guid = str(uuid4())
    schema_obj.guid = guid
    assert schema_obj.guid == guid
    assert schema_obj.init_guid_1 == "bebe8b34-b12e-4fda-b00c-99979452b7bd"
    assert schema_obj.init_guid_2 == "84b022bd-2b00-4b62-8539-4ec07887bbe4"


def test_016_validate_dict_type():
    """
    SCM-016
    *Test case for validating dict type *

    **Test Scenario:**

    #. Create schema with dict parameter[P1], should succeed.
    #. Try to set parameter[P1] with non dict type, should fail.
    #. Try to set parameter[P1] with dict type, should succeed.
    """
    log("Create schema with dict parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    info = (dict)
    init_dict = {"number": 468} (dict)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non dict type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.info = random_string()

    with T.assertRaises(Exception):
        schema_obj.info = random.randint(1, 1000)

    with T.assertRaises(Exception):
        schema_obj.info = random.uniform(1, 100)

    with T.assertRaises(Exception):
        schema_obj.info = [random.randint(1, 100), random.randint(1, 100)]
    log("Try to set parameter[P1] with dict type, should succeed.")
    value = random.randint(1, 1000)
    schema_obj.info = {"number": value}
    assert schema_obj.info == {"number": value}
    assert schema_obj.init_dict == {"number": 468}


def test_017_validate_hash_type():
    """
    SCM-017
    *Test case for validating hash type *

    **Test Scenario:**

    #. Create schema with hash parameter[P1], should succeed.
    #. Try to set parameter[P1] with non hash type, should fail.
    #. Try to set parameter[P1] with hash type, should succeed.
    """
    log("Create schema with hash parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    data = (h)
    init_hash = 46:682 (h)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non hash type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.data = [random.randint(1, 100), random.randint(10, 1000), random.randint(1, 500)]

    with T.assertRaises(Exception):
        schema_obj.data = random_string()

    with T.assertRaises(Exception):
        schema_obj.data = random.uniform(1, 100)

    with T.assertRaises(Exception):
        schema_obj.data = {"number": random.randint(1, 100)}
    log("Try to set parameter[P1] with hash type, should succeed.")
    data = (random.randint(1, 1000), random.randint(1000, 1000000))
    schema_obj.data = data
    assert schema_obj.data == data

    data = [random.randint(1, 100), random.randint(1, 100)]
    schema_obj.data = data
    assert schema_obj.data[0] == data[0]
    assert schema_obj.data[1] == data[1]
    assert schema_obj.init_hash == (46, 682)


def test_018_validate_multiline_type():
    """
    SCM-018
    *Test case for validating multiline type *

    **Test Scenario:**

    #. Create schema with multiline parameter[P1], should succeed.
    #. Try to set parameter[P1] with non multiline type, should fail.
    #. Try to set parameter[P1] with multiline type, should succeed.
    """
    log("Create schema with multiline parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    lines = (multiline)
    init_mline = "example \\n example2 \\n example3" (multiline)

    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non multiline type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.lines = random_string()

    with T.assertRaises(Exception):
        schema_obj.lines = random.randint(1, 1000)

    with T.assertRaises(Exception):
        schema_obj.lines = random.uniform(1, 100)

    with T.assertRaises(Exception):
        schema_obj.lines = [random.randint(1, 100), random.randint(1, 100)]

    with T.assertRaises(Exception):
        schema_obj.lines = {"number": random.randint(1, 100)}
    log("Try to set parameter[P1] with multiline type, should succeed.")
    schema_obj.lines = "example \n example2 \n example3"
    assert schema_obj.lines == "example \n example2 \n example3"
    assert schema_obj.init_mline == "example \\n example2 \\n example3"


def test_019_validate_yaml_type():
    """
    SCM-019
    *Test case for validating yaml type *

    **Test Scenario:**

    #. Create schema with yaml parameter[P1], should succeed.
    #. Try to set parameter[P1] with yaml type, should succeed.
    """
    log("Create schema with yaml parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    data = (yaml)
    init_yaml = {'example':'test1'} (yaml)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non yaml type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.data = "{test"

    log("Try to set parameter[P1] with yaml type, should succeed.")
    data = random_string()
    schema_obj.data = data
    assert schema_obj.data == data

    y = """
example:
- test"""
    schema_obj.data = y
    assert schema_obj.data == {"example": ["test"]}
    assert schema_obj.init_yaml == {"example": "test1"}


def test_020_validate_enum_type():
    """
    SCM-020
    *Test case for validating enum type *

    **Test Scenario:**

    #. Create schema with enum parameter[P1], should succeed.
    #. Try to set parameter[P1] with non enum type, should fail.
    #. Try to set parameter[P1] with enum type, should succeed.
    """
    log("Create schema with enum parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    colors = 'red, green, blue, black' (E)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non enum type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.colors = random_string()

    with T.assertRaises(Exception):
        schema_obj.colors = random.randint(5, 1000)

    with T.assertRaises(Exception):
        schema_obj.colors = random.uniform(5, 100)

    with T.assertRaises(Exception):
        schema_obj.colors = ["RED", "GREEN", "BLUE", "BLACK"]

    with T.assertRaises(Exception):
        schema_obj.colors = {"colors": ["RED", "GREEN", "BLUE", "BLACK"]}
    log("Try to set parameter[P1] with enum type, should succeed.")
    colors = ["RED", "GREEN", "BLUE", "BLACK"]
    color = random.choice(colors)
    schema_obj.colors = color
    assert schema_obj.colors == color

    index = random.randint(0, 3)
    schema_obj.colors = index
    assert schema_obj.colors == colors[index]


def test_021_validate_binary_type():
    """
    SCM-021
    *Test case for validating binary type *

    **Test Scenario:**

    #. Create schema with binary parameter[P1], should succeed.
    #. Try to set parameter[P1] with non binary type, should fail.
    #. Try to set parameter[P1] with binary type, should succeed.
    """
    log("Create schema with binary parameter[P1], should succeed.")
    scm = """
    @url = test.schema
    binary = (bin)
    init_bin = 'this is binary' (bin)
    """
    schema_nw = schema(scm)
    schema_obj = schema_nw.new()

    log("Try to set parameter[P1] with non binary type, should fail.")
    with T.assertRaises(Exception):
        schema_obj.binary = random.randint(1, 1000)

    with T.assertRaises(Exception):
        schema_obj.binary = random.uniform(1, 100)

    with T.assertRaises(Exception):
        schema_obj.binary = [random_string().encode(), random_string().encode()]

    with T.assertRaises(Exception):
        schema_obj.binary = {"binary": random_string().encode()}

    log("Try to set parameter[P1] with binary type, should succeed.")
    binary = random_string().encode()
    schema_obj.binary = binary
    assert schema_obj.binary == binary
    assert schema_obj.init_bin == b"\xb6\x18\xac\x8a\xc6\xe2\x9d\xaa\xf2"
