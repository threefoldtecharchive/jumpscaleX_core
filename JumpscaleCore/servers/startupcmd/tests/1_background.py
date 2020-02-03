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

startupcmd = j.servers.startupcmd


def test_background():
    """
    to run:

    kosmos 'j.servers.startupcmd.test(name="background")' --debug
    """

    startupcmd.http_back.cmd_start = "python3 -m http.server"  # starts on port 8000
    startupcmd.http_back.ports = 8000
    startupcmd.http_back.executor = "background"
    startupcmd.http_back.timeout = 5
    startupcmd.http_back.start()
    assert startupcmd.http_back.pid
    assert startupcmd.http_back.is_running() is True
    startupcmd.http_back.stop()
    assert startupcmd.http_back.is_running() is False

    return "OK"
