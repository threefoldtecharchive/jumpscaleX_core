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

    kosmos 'j.data.schema.test(name="load_data")'

    test loading of data from toml source

    """

    toml = """
        enable = true
        # unique name with dot notation for the package
        name = "digitalme.base"


        [[loaders]]
        giturl = "https://github.com/threefoldtech/digital_me/tree/development960/packages/system/base"
        dest = ""

        [[loaders]]
        giturl = "https://github.com/threefoldtech/jumpscale_weblibs/tree/master/static"
        dest = "blueprints/base/static"

        """

    schema_package = """
        @url =  jumpscale.digitalme.package
        name = "UNKNOWN" (S)           #official name of the package, there can be no overlap (can be dot notation)
        enable = true (B)
        args = (LO) !jumpscale.digitalme.package.arg
        loaders= (LO) !jumpscale.digitalme.package.loader

        @url =  jumpscale.digitalme.package.arg
        key = "" (S)
        val =  "" (S)

        @url =  jumpscale.digitalme.package.loader
        giturl =  "" (S)
        dest =  "" (S)
        enable = true (B)

        # ENDSCHEMA

        """
    data = j.data.serializers.toml.loads(toml)

    schema_object = j.data.schema.get_from_text(schema_package)
    data = schema_object.new(datadict=data)

    # TODO: needs some tests here

    self._log_info("TEST DONE LOAD DATA")

    return "OK"
