from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.tools.threebot.test(name="serialization")'

    """

    data_list = self._get_test_data()
    res_j = self._serialize(data_list, serialization_format="json")
    print(res_j)
    p = '[true, 1, [1, 2, "a"], [999, "090f7be0270b7ec77fbc8ac448c516e6", "{\\"name\\": \\"aname\\", \\"description\\": \\"something\\"}"], "astring", [998, {"a": 2}]]'

    assert res_j == p
    res_mp = self._serialize(data_list, serialization_format="msgpack")
    print(res_mp)
    q = b'\x96\xc3\x01\x93\x01\x02\xa1a\x93\xcd\x03\xe7\xd9 090f7be0270b7ec77fbc8ac448c516e6\xd9-{"name": "aname", "description": "something"}\xa7astring\x92\xcd\x03\xe6\x81\xa1a\x02'

    assert res_mp == q

    un_res_mp = self._unserialize(res_mp, serialization_format="msgpack")
    print(un_res_mp)

    assert un_res_mp == data_list
    print("test with json format")
    un_res_j = self._unserialize(res_j, serialization_format="json")
    print(un_res_j)

    for idx, val in enumerate(data_list):
        if not val == un_res_j[idx]:
            assert val.__str__() == un_res_j[idx].replace('"', "'")

    # CLEAN STATE
    self._log_info("TEST serialization DONE")
    return "OK"
