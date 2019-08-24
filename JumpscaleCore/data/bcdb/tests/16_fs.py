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

    kosmos 'j.data.bcdb.test(name="fs")'

    """
    tags = ["color:blue", "color:white", "font:arial", "font:tahoma", "style:italian"]
    types = ["md", "pdf", "xls", "doc", "jpg"]
    contents = ["threefold foundation", "the new internet", "change the world", "digital freedom", "the future of IT"]
    bcdb = j.data.bcdb.new("test_fs", reset=True)

    bcdb.models_add_threebot()

    cl = j.clients.sonic.get_client_bcdb()
    cl.flush("test_fs")

    block_model = bcdb.model_get(url="jumpscale.bcdb.fs.block.2")
    file_model = bcdb.model_get(url="jumpscale.bcdb.fs.file.2")
    dir_model = bcdb.model_get(url="jumpscale.bcdb.fs.dir.2")

    root = dir_model.new()
    root.name = "/"
    root.save()

    for i in range(1, 6):

        parent = dir_model.new()
        parent.name = "{}{}/".format(root.name, i)
        parent.save()
        root.dirs.append(parent.id)

        # create subdirs
        for k in range(1, 6):
            subdir = dir_model.new()
            subdir.name = "{}dir_{}/".format(parent.name, k)
            subdir.save()
            parent.dirs.append(subdir.id)

        # create files
        for k in range(1, 6):
            file = file_model.new()
            file.name = "{}file_{}".format(parent.name, k)
            file.content = contents[(k - 1) % 5]
            file.type = types[(k - 1) % 5]
            file.tags.append(tags[(k - 1) % 5])
            file.dir_id = parent.id
            file.size_bytes = len(file.content.encode())
            file.save()
            parent.files.append(file.id)

        parent.save()
    root.save()
    res = file_model.files_search(tags="color:blue")
    assert len(res) == 5
    res = file_model.files_search(type="md")
    assert len(res) == 5
    res = file_model.files_search(content="threefold")
    assert len(res) == 5
    res = file_model.files_search(tags="color:blue", type="pdf")
    assert len(res) == 0
    res = file_model.files_search(tags="color:blue", type="md")
    assert len(res) == 5

    start_cmd = """
    from Jumpscale import j
    rack = j.servers.rack.get()
    from jumpscale.Jumpscale.data.bcdb.connectors.webdav.BCDBFSProvider import BCDBFSProvider
    
    rack.webdav_server_add(webdavprovider=BCDBFSProvider("test_fs"), port=4444)
    rack.start()
    """

    s = j.servers.startupcmd.get(
        name="webdav_fs_test", cmd_start=start_cmd, interpreter="python", executor="tmux", ports=[4444]
    )
    s.start()
    print("Dav server running on port 4444")
