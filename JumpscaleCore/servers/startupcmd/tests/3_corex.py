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

    kosmos 'j.data.schema.test(name="corex")' --debug
    """

    j.servers.corex.default.check()
    corex = j.servers.corex.default.client

    self.http.executor = "corex"
    self.http.corex_client_name = corex.name
    self.http.timeout = 5
    self.http.delete()
    self.http.cmd_start = "python3 -m http.server"  # starts on port 8000
    self.http.executor = "corex"
    self.http.corex_client_name = corex.name
    self.http.start()

    self.http.monitor.ports = 8000

    j.shell()
    self.http.stop()
    self.http.delete()

    return "OK"
