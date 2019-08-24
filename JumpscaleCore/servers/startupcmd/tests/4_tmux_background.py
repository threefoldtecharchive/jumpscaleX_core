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
there are issues when running on console
no need to run, but we leave it here, its a good reference
"""

START_BASH = """
    set -x

    if [ "$1" == "kill" ] ; then
        js_shell 'j.servers.tmux.kill()' || exit 1
        exit 1
    fi

    tmux -f /sandbox/cfg/.tmux.conf has-session
    if [ "$?" -eq 1 ] ; then
        echo "no server running need to start"
        tmux -f /sandbox/cfg/.tmux.conf new -s main -d 'bash --rcfile /sandbox/bin/env_tmux_detach.sh'
    else
        echo "tmux session already exists"
    fi

    if [ "$1" != "start" ] ; then
        tmux a
    fi

    """


def main(self):
    """
    to run:

    kosmos 'j.data.schema.test(name="corex")' --debug
    """
    return "OK"

    self.tmuxserver.delete()
    startup_cmd = self.tmuxserver  # grab an instance
    startup_cmd.executor = "foreground"  # because detaches itself automatically
    startup_cmd.interpreter = "direct"
    startup_cmd.cmd_start = j.core.text.strip(START_BASH)
    startup_cmd.timeout = 5

    startup_cmd.monitor.process_strings_regex = "^tmux"

    startup_cmd.start()
    assert startup_cmd.is_running() == True
    assert startup_cmd.pid

    r = startup_cmd.stop()

    assert startup_cmd.is_running() == False

    return "OK"
