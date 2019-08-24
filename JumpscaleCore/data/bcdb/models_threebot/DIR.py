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


class DIR(j.data.bcdb._BCDBModelClass):
    def _schema_get(self):
        return j.data.schema.get_from_url("jumpscale.bcdb.fs.dir.2")

    _file_model_ = None

    @property
    def _file_model(self):
        if not self._file_model_:
            self._file_model_ = self.bcdb.model_get_from_file("{}/models_threebot/DIR.py".format(self.bcdb._dirpath))
        return self._file_model_

    def _create_root_dir(self):
        new_dir = self.new()
        new_dir.name = "/"
        new_dir.save()
        return new_dir

    def create_empty_dir(self, name, create_parent=True):
        if name == "/" and not len(self.get_by_name(name="/")) > 0:
            return self._create_root_dir()
        if name == "/":
            return self.get_by_name("/")[0]
        parent_path = j.sal.fs.getParent(name)
        parent = self.get_by_name(name=parent_path)
        if len(parent) == 0 and create_parent:
            parent = [self.create_empty_dir(parent_path, create_parent=True)]
        if len(parent) == 0:
            raise j.exceptions.Base("can't find {}".format(parent_path))
        parent = parent[0]
        new_dir = self.new()
        path = j.sal.fs.pathClean(j.sal.fs.joinPaths(parent.name, name))
        new_dir.name = path
        new_dir.save()
        parent.dirs.append(new_dir.id)
        parent.save()
        return new_dir

    def delete_recursive(self, name):
        name = j.sal.fs.pathClean(name)
        dir = self.get_by_name(name=name)[0]
        for file_id in dir.files:
            self._file_model.get(file_id).delete()

        for dir_id in dir.dirs:
            self.delete_recursive(self.get(dir_id).name)

        dir.delete()
