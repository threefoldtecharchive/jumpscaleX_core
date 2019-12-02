from Jumpscale import j


class DIR(j.data.bcdb._BCDBModelClass):
    def _schema_get(self):
        return j.data.schema.get_from_url("jumpscale.bcdb.fs.dir.2")

    _file_model_ = None

    @property
    def _file_model(self):
        if not self._file_model_:
            self._file_model_ = self.bcdb.model_get_from_file("{}/models_threebot/FILE.py".format(self.bcdb._dirpath))
        return self._file_model_

    def _create_root_dir(self):
        new_dir = self.new()
        new_dir.name = "/"
        new_dir.save()
        return new_dir

    def create_empty_dir(self, name, create_parent=True):
        if self.get_by_name(name=name, die=False):
            return name
        if name == "/":
            try:
                return self.get_by_name(name="/")
            except j.exceptions.NotFound:
                return self._create_root_dir()
        if name == "/":
            return self.get_by_name("/")
        parent_path = j.sal.fs.getParent(name)
        parent = self.get_by_name(name=parent_path, die=False)
        if not parent and create_parent:
            parent = self.create_empty_dir(parent_path, create_parent=True)

        if not parent:
            raise j.exceptions.Base("can't find {}".format(parent_path))

        new_dir = self.new()
        path = j.sal.fs.pathClean(j.sal.fs.joinPaths(parent.name, name))
        new_dir.name = path
        new_dir.save()
        parent.dirs.append(new_dir.id)
        parent.save()
        return new_dir

    def delete_recursive(self, name):
        name = j.sal.fs.pathClean(name)
        dir = self.get_by_name(name=name)
        for file_id in dir.files:
            self._file_model.get(file_id).delete()

        for dir_id in dir.dirs:
            self.delete_recursive(self.get(dir_id).name)

        # delete the dir id from parent
        parent_path = j.sal.fs.getParent(name)
        if parent_path:
            parent = self.get_by_name(name=parent_path)
            parent.dirs.remove(dir.id)
            parent.save()

        dir.delete()
