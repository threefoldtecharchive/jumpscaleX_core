from Jumpscale import j


def test_serialization():
    """
    to run:
    kosmos 'j.me.test(name="serialization")'
    """

    data_list = j.me._get_test_data()
    res_j = j.me._serialize(data_list, serialization_format="json")

    print(res_j)
    p = '[true, 1, [1, 2, "a"], [999, "f47f5adfee782b7059616c42b5c10fab", "{\\"name\\": \\"aname\\", \\"description\\": \\"something\\"}"], "astring", [998, {"a": 2}]]'

    assert res_j == p
    res_mp = j.me._serialize(data_list, serialization_format="msgpack")
    print(res_mp)
    q = b'\x96\xc3\x01\x93\x01\x02\xa1a\x93\xcd\x03\xe7\xd9 f47f5adfee782b7059616c42b5c10fab\xd9-{"name": "aname", "description": "something"}\xa7astring\x92\xcd\x03\xe6\x81\xa1a\x02'

    assert res_mp == q

    un_res_mp = j.me._unserialize(res_mp, serialization_format="msgpack")
    print(un_res_mp)

    assert un_res_mp == data_list
    print("test with json format")
    un_res_j = j.me._unserialize(res_j, serialization_format="json")
    print(un_res_j)

    for idx, val in enumerate(data_list):
        if not val == un_res_j[idx]:
            assert val.__str__() == un_res_j[idx].replace('"', "'")

    # CLEAN STATE
    return "OK"