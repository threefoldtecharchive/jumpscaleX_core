from Jumpscale import j

# THIS IS A LICENSE EDITING TOOLS THE BLOCKS BELOW IMPLY NOTHING RELATED TO LICENSES

TFTECH = "# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/"

TFTECH_OTHER = """
# Copyright (C) before July 2018 : companies related to Incubaid NV e.g Qlayer NV and GIG Technologies using Apache 2 license
# Copyright (C) July 2018 :  TF TECH NV in Belgium see https://www.threefold.tech/, all modifications made by TF TECH NV are GPL v3
"""


GPL3 = """
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
"""


JSBASE = j.baseclasses.object


class FixerReplacer(j.baseclasses.object):
    def file_remove_license(self, C, tofind):
        if C.find("file_remove_license") != -1:
            return False, ""
        if C.find(tofind) != -1:
            out = ""
            state = "start"
            for line in C.split("\n"):
                if line.startswith(tofind):
                    state = "license"
                    continue
                if state == "license":
                    if line.strip() == "":
                        continue
                    else:
                        state = "ok"
                if state == "ok":
                    out += line + "\n"
            return True, out
        return False, C

    def file_process(self, path, write=False, header=None, addlicense=True):
        assert header
        out = ""
        C = j.sal.fs.readFile(path)

        rc = True
        while rc:
            rc, C = self.file_remove_license(C, "# LICENSE END")
        # rc = True
        # while rc:
        #     rc, C = self.file_remove_license(C, "# You should have received")
        # rc = True
        # while rc:
        #     rc, C = self.file_remove_license(C, "# along with")
        if addlicense:
            C4 = header + GPL3 + "\n\n" + C
        else:
            C4 = C
        self._log_info("will copyright:%s" % path)
        if write:
            j.sal.fs.writeFile(path, C4)

    def dir_process(self, path, extensions=["py"], recursive=True, write=False, header=None, addlicense=True):
        if not header:
            header = TFTECH
        header = header.rstrip()
        path = j.sal.fs.pathNormalize(path)
        for ext in extensions:
            for p in j.sal.fs.listFilesInDir(path, recursive=recursive, filter="*.%s" % ext, followSymlinks=False):
                self._log_debug("process file:%s" % p)
                self.file_process(path=p, write=write, header=header, addlicense=addlicense)
