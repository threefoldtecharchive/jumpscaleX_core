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
import requests


def main(self):
    """
    to run:
    kosmos 'j.data.bcdb.test(name="webdav")'

    """

    # md5 = "cbf134f55d0c7149ef188cf8a52db0eb"
    # sid = "7"
    test_cmd = """
    from Jumpscale import j
    bcdb = j.data.bcdb.new("test", reset=True)
    vfs = j.data.bcdb._get_vfs()
    
    SCHEMA = \"\"\"
    @url = threefoldtoken.wallet.test
    name** = "wallet"
    addr = ""                   # Address
    ipaddr = (ipaddr)           # IP Address
    email = "" (S)              # Email address
    username = "" (S)           # User name
    
    \"\"\"
    m_wallet_test = bcdb.model_get(schema=SCHEMA)
    for i in range(10):
        o = m_wallet_test.new()
        assert o._model.schema.url == "threefoldtoken.wallet.test"
        o.addr = "something:%s" % i
        o.email = "myemail%s@test.fr" % i
        o.name = "myuser_%s" % i
        o.username = "nothing here_%s" % i
        o.save()
    
    from Jumpscale.data.bcdb.connectors.webdav.BCDBResourceProvider import BCDBResourceProvider
    rack = j.servers.rack.get()
    rack.webdav_server_add(webdavprovider=BCDBResourceProvider())
    rack.start()
    """
    s = j.servers.startupcmd.get(
        name="webdav_test", cmd_start=test_cmd, interpreter="python", executor="tmux", ports=[4443]
    )
    s.start()
    session = requests.session()
    session.auth = requests.auth.HTTPBasicAuth("root", "root")

    # test get schema by url
    schema = session.get("http://0.0.0.0:4443/test/schemas/threefoldtoken.wallet.test").json()
    assert schema["url"] == "threefoldtoken.wallet.test"

    # test get data by url
    data = session.get("http://0.0.0.0:4443/test/data/1/threefoldtoken.wallet.test/1").json()
    assert data["name"] == "myuser_0"
    assert data["id"] == 1

    """  
    data["email"] = "yolo@nofear.com"
    session.auth = requests.auth.HTTPBasicAuth("root", "root")
    put = session.put("http://0.0.0.0:4443/test/data/1/threefoldtoken.wallet.test/1", data)
    print(put)
    j.shell()
    data.pop("id")
    data["email"] = "new@one.com"
    post = session.post("http://0.0.0.0:4443/test/data/1/threefoldtoken.wallet.test", data)
    print(post)
    delete = session.delete("http://0.0.0.0:4443/test/data/1/threefoldtoken.wallet.test/1")
    print(delete) """
    web_dav = j.servers.startupcmd.get("webdav_test")
    web_dav.stop()
    web_dav.wait_stopped()

    self._log_info("test ok")
