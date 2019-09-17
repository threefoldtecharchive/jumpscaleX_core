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


from .StartupCMD import StartupCMD

from Jumpscale import j
import time


class StartupCMDFactory(j.baseclasses.object_config_collection_testtools):

    _CHILDCLASS = StartupCMD
    __jslocation__ = "j.servers.startupcmd"

    def _init(self, **kwargs):
        tdir = j.sal.fs.joinPaths(j.sal.fs.joinPaths(j.dirs.VARDIR, "cmds"))
        j.sal.fs.createDir(tdir)

        self._cmdsdir = tdir

    def test(self):
        """
        kosmos 'j.servers.startupcmd.test()'
        :return:
        """

        def http_tmux():
            self.http.delete()
            self.http.cmd_start = "python3 -m http.server"  # starts on port 8000
            self.http.ports = 8000
            self.http.start()
            assert self.http.pid
            self.http.timeout = 5
            assert self.http.is_running()
            self.http.stop()
            assert not self.http.is_running()
            # self.http.delete()

        def http_back():
            self.http_back.delete()
            self.http_back.cmd_start = "python3 -m http.server"  # starts on port 8000
            self.http_back.ports = 8000
            self.http_back.executor = "background"
            self.http_back.timeout = 5
            self.http_back.start()
            assert self.http_back.pid
            assert self.http_back.is_running() == True
            self.http_back.stop()
            assert self.http_back.is_running() == False
            self.http_back.delete()

        def http_corex():
            # make sure corex is there
            j.servers.corex.default.start()
            corex = j.servers.corex.default.client
            self.http.interpreter = "direct"
            self.http.ports = 8000
            self.http.executor = "corex"
            self.http.corex_client_name = corex.name
            self.http.timeout = 5
            self.http.cmd_start = "python3 -m http.server"  # starts on port 8000

            self.http.start()
            assert self.http.is_running() == True
            assert self.http.pid

            r = self.http.stop()

            assert self.http.is_running() == False
            self.http.delete()

        # NOT WORKING, SOMETHING WEIRD
        def tmux_background():
            C = """
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
            self.tmuxserver.delete()
            startup_cmd = self.tmuxserver  # grab an instance
            startup_cmd.executor = "foreground"  # because detaches itself automatically
            startup_cmd.interpreter = "direct"
            startup_cmd.process_strings_regex = "^tmux"
            startup_cmd.cmd_start = j.core.text.strip(C)
            startup_cmd.timeout = 5

            startup_cmd.start()
            assert startup_cmd.is_running() == True
            assert startup_cmd.pid

            r = startup_cmd.stop()

            assert startup_cmd.is_running() == False

        http_tmux()
        http_back()
        http_corex()

        tmux_background()

        self.http.delete()
        self.tmuxserver.delete()
        self.http_back.delete()

        print("TEST STARTUPCMDS OK")
