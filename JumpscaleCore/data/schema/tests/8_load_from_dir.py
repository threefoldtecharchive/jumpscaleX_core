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

    kosmos 'j.data.schema.test(name="load_from_dir")' --debug
    """
    j.data.schema.reset()
    mpath = self._dirpath + "/tests/schemas_toml"
    assert j.sal.fs.exists(mpath)

    j.data.schema.add_from_path(mpath)

    assert len(j.data.schema._url_to_md5) == 4
    assert len(j.data.schema._md5_to_schema) == 4

    s = j.data.schema.get_from_url("threefoldtoken.wallet")

    assert len(s.properties_index_keys) == 1
    assert len(s.properties) == 5

    assert s.systemprops.importance == "true"

    assert len(s.systemprops.__dict__.keys()) == 2

    r = """
    ## SCHEMA: threefoldtoken.wallet

    prop:jwt                       string
    prop:addr                      string
    prop:ipaddr                    ipaddr
    prop:email                     string
    prop:username                  string
    
    ### systemprops:
    
    importance:true
    systemprop:1
    """

    assert j.core.text.strip_to_ascii_dense(r) == j.core.text.strip_to_ascii_dense(str(s))

    s2 = j.data.schema.get_from_md5(s._md5)

    assert s2 == s

    s3 = j.data.schema.get_from_text(s2.text)
    assert s2 == s3

    assert s2 == j.data.schema.get_from_url(s.url)

    self._log_info("load from dir ok")
    # CLEAN STATE
    # j.data.schema.remove_from_text(s2.text)
