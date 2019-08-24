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
from wsgidav import compat, util
from wsgidav.dav_provider import DAVCollection, DAVNonCollection, DAVProvider


class DirCollection(DAVCollection):
    """
    Handles all kinds of directory-like resources
    """

    def __init__(self, path, environ):
        DAVCollection.__init__(self, path, environ)
        self.vfs = self.provider.vfs

    def get_member_names(self):
        """
        get member names to be listed from the path
        :return: list of member names
        """
        names = self.vfs.list(self.path)
        res = []
        for name in names:
            try:
                json_data = j.data.serializers.json.loads(name)
                if "id" in json_data:
                    res.append(str(json_data["id"]))
                elif "name" in json_data:
                    res.append(json_data["name"])
                else:
                    res.append(name)
            except:
                res.append(name)
        return res

    def get_member(self, name):
        """
        get member by name
        :param name: member name
        :return: DirCollection if the member is a dir-like or DocResource if the member is a doc
        """
        path = j.sal.fs.joinPaths(self.path, name)

        # This to avoid returning 500 response if there was an error in bcdb returned data
        try:
            vfile = self.vfs.get(path)
        except Exception as e:
            return CorruptedResource(path, self.environ, str(e))

        if vfile.is_dir:
            return DirCollection(path, self.environ)
        else:
            return DocResource(path, self.environ, vfile)


class CorruptedResource(DAVNonCollection):
    """
    Represents a corrupted resource which could happen because of bcdb failure
    """

    def __init__(self, path, environ, error):
        DAVNonCollection.__init__(self, path, environ)
        self.path = path
        self.error = error

    def get_content(self):
        html = "<pre>" + self.error + "</pre>"
        return compat.BytesIO(html.encode("utf-8"))

    def get_content_length(self):
        return len(self.get_content().read())

    def get_content_type(self):
        return "text/html"

    def get_display_name(self):
        return compat.to_native(self.path + " --corrupted")

    def get_display_info(self):
        return {"type": "Corrupted resource"}


class DocResource(DAVNonCollection):
    """
    Handles docs. a doc is bcdb data object treated like a documentation
    """

    def __init__(self, path, environ, vfile):
        DAVNonCollection.__init__(self, path, environ)
        self.doc = vfile.get()
        self._title = None

    @property
    def title(self):
        if not self._title:
            try:
                json_data = j.data.serializers.json.loads(self.doc)
                if "name" in json_data.keys():
                    self._title = json_data["name"]
                elif "id" in json_data.keys():
                    self._title = json_data["id"]
                elif "url" in json_data.keys():
                    self._title = json_data["url"]
                else:
                    self._title = self.doc[:15]
            except:
                self._title = self.doc[:15]

        return self._title

    def get_content(self):
        html = self.doc
        return compat.BytesIO(html.encode("utf-8"))

    def get_content_length(self):
        return len(self.get_content().read())

    def get_content_type(self):
        try:
            j.data.serializers.json.loads(self.doc)
            return "application/json"
        except:
            return "text/html"

    def get_display_name(self):
        return compat.to_native(self.title)

    def get_display_info(self):
        return {"type": "resource"}


class BCDBResourceProvider(DAVProvider):
    def __init__(self):
        DAVProvider.__init__(self)
        self.vfs = j.data.bcdb._get_vfs()

    def get_resource_inst(self, path, environ):
        """
        Return DAVResource object for path.
        """
        root = DirCollection("/", environ)
        return root.resolve("/", path)
