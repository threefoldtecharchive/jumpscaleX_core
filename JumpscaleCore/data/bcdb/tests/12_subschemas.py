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

"""
aim is to see if the subschema's are loaded properly in the metadata db
"""


def main(self):
    """
    to run:
    kosmos 'j.data.bcdb.test(name="subschemas")'

    """

    schema = """
    
            @url = jsx.master.1
            cmds = (LO) !jsx.subschema.1
            cmd = (O) !jsx.subschema.2
            deepper = (O) !jsx.subschema.3

    
            @url = jsx.subschema.1
            name = ""
            comment = ""

            @url = jsx.subschema.2
            name2 = ""
            comment2 = ""

            @url = jsx.subschema.3
            name3 = ""
            comment3 = ""
            cmds = (LO) !jsx.subschema.3.1
            cmd = (O) !jsx.subschema.3.2            

            @url = jsx.subschema.3.1
            name31 = ""
            comment31 = ""    
            cmds = (LO) !jsx.subschema.3.1.1
            cmd = (O) !jsx.subschema.3.1.2         

            @url = jsx.subschema.3.1.1
            name311 = ""
            comment311 = ""    

            @url = jsx.subschema.3.1.2
            name312 = ""
            comment312 = ""    
            
            @url = jsx.subschema.3.2.1
            name321 = ""
            comment321 = ""    

            @url = jsx.subschema.3.2.2
            name322 = ""
            comment322 = ""    
                
    
            @url = jsx.subschema.3.2
            name31 = ""
            comment31 = ""    
            cmds = (LO) !jsx.subschema.3.2.1
            cmd = (O) !jsx.subschema.3.2.2 
        
        """

    # bcdb = j.data.bcdb.get("test")
    bcdb, model = self._load_test_model(type="sqlite")
    bcdb.reset()
    m = bcdb.model_get(schema=schema)

    urls = []
    urls.append("jsx.master.1")
    urls.append("jsx.subschema.1")
    urls.append("jsx.subschema.2")
    urls.append("jsx.subschema.3")
    urls.append("jsx.subschema.3.1")
    urls.append("jsx.subschema.3.1.1")
    urls.append("jsx.subschema.3.1.2")
    urls.append("jsx.subschema.3.2")
    urls.append("jsx.subschema.3.2.1")
    urls.append("jsx.subschema.3.2.2")

    for url in urls:
        md5 = j.data.schema._url_to_md5[url]
        s = bcdb.schema_get(md5=md5)  # need to start from bcdb
        assert s._md5 == md5

        bcdb.meta._schema_exists(s._md5)
        assert s._md5 == md5
        assert s.url == url

    return "OK"
