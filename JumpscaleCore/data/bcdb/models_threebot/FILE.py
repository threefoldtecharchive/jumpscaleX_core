from Jumpscale import j
from wsgidav import compat
import mimetypes
import types


class FILE(j.data.bcdb._BCDBModelClass):
    def _schema_get(self):
        return j.data.schema.get_from_url("jumpscale.bcdb.fs.file.2")

    _dir_model_ = None

    @property
    def _dir_model(self):
        if not self._dir_model_:
            self._dir_model_ = self.bcdb.model_get_from_file("{}/models_threebot/DIR.py".format(self.bcdb._dirpath))
        return self._dir_model_

    _block_model_ = None

    @property
    def _block_model(self):
        if not self._block_model_:
            self._block_model_ = self.bcdb.model_get_from_file("{}/models_threebot/BLOCK.py".format(self.bcdb._dirpath))
        return self._block_model_

    def _text_index_content_pre_(self, property_name, val, obj_id, nid=1):
        """

        :return: text


        text e.g. : color__red ftype__doc importance__1

        """
        if property_name == "tags":
            obj = self.get(obj_id)
            out = ""
            for tag in obj.tags:
                out += tag.replace(":", "__") + " "
            # Add more meta data as tags
            type = str(obj.type).lower()
            if type:
                out += "type__%s " % type
            ext = str(obj.extension).lower()
            if ext:
                out += "ext__%s " % ext
            val = out
        return property_name, val, obj_id, nid

    def files_search(self, type=None, tags=None, content=None, description=None, extension=None):
        return list(
            self._do_search(**dict(type=type, tags=tags, extension=extension, content=content, description=description))
        )

    def _do_search(self, **kwargs):
        if not kwargs:
            return None

        key, value = kwargs.popitem()
        if not value:
            return self._do_search(**kwargs)

        if key == "tags":
            value = value.replace(":", "__")
        if key == "type":
            key = "tags"
            value = "type__%s" % value.lower()

        if key == "extension":
            key = "tags"
            value = "ext__%s" % value.lower()

        res = self.search(value, property_name=key)
        next = self._do_search(**kwargs)
        if next is not None and res:
            return set(res).intersection(next)
        else:
            return set(res)

    def filestream_get(self, vfile):
        return FileStream(vfile)

    def file_create_empty(self, name, create_parent=True):
        """
        create new file inside a directory
        :param name: file name
        :return: file object
        """
        new_file = self.new()
        name = j.sal.fs.pathClean(name)
        new_file.name = name
        new_file.save()
        dir = self._dir_model.get_by_name(name=j.sal.fs.getParent(name), die=False)
        if not dir:
            dir = self._dir_model.create_empty_dir(j.sal.fs.getParent(name))
        dir.files.append(new_file.id)
        dir.save()
        return new_file

    def file_write(self, path, content, append=False, create=True):
        """
        writes a file to bcdb
        :param path: the path to store the file
        :param content: content of the file to be written
        :param append: if True will append if the file already exists
        :param create: create new if true and the file doesn't exist
        :return: file object
        """
        path = j.sal.fs.pathClean(path)
        file = self.get_by_name(name=path, die=not create)  # die if create=False and file not found

        # file not found, & create=True
        if not file:
            file = self.file_create_empty(path)

        fs = FileStream(file)
        fs.writelines(content, append=append)
        fs.close()
        return file

    def file_delete(self, path):
        path = j.sal.fs.pathClean(path)
        file = self.get_by_name(name=path)
        file.delete()
        parent = j.sal.fs.getParent(path)
        parent = j.sal.fs.pathClean(parent)
        parent = self._dir_model.get_by_name(name=parent)
        parent.files.remove(file.id)
        parent.save()

    def file_read(self, path):
        path = j.sal.fs.pathClean(path)
        file = self.get_by_name(name=path)

        fs = FileStream(file)
        return fs.read_stream_get().read()


class FileStream:
    # plain types are the the file types that will be stored as plain text in content
    # other types will be saved in blocks
    PLAIN_TYPES = ["md", "txt", "json", "toml"]
    BLOCK_SIZE = 8192

    def __init__(self, vfile):
        self._vfile = vfile
        self._bcdb = self._vfile._model.bcdb

    _block_model_ = None

    @property
    def _block_model(self):
        if not self._block_model_:
            self._block_model_ = self._bcdb.model_get(url="jumpscale.bcdb.fs.block.2")
        return self._block_model_

    def writelines(self, stream, append=True):
        ext = self._vfile.extension or self._vfile.name.split(".")[-1]
        if (ext in self.PLAIN_TYPES and getattr(stream, "readlines", None)) or isinstance(stream, str):
            self._save_plain(stream, append=append)
        else:
            self._save_blocks(stream, append=append)

        if not self._vfile.extension and ext:
            self._vfile.extension = ext
            self._vfile.save()

    def _drain_response(self, response_generator):
        while True:
            try:
                yield next(response_generator)
            except StopIteration:
                yield None

    def _drain_stream(self, stream):
        block = stream.read(self.BLOCK_SIZE)
        while block:
            yield block
            block = stream.read(self.BLOCK_SIZE)
        yield None

    def _save_blocks(self, stream, append=True):
        if not append:
            for block_id in self._vfile.blocks:
                block = self._block_model.get(block_id)
                block.delete()
            self._vfile.blocks.clear()
            self._vfile.save()

        if hasattr(stream, "iter_content"):
            response_generator = stream.iter_content(self.BLOCK_SIZE)
            blocks_generator = self._drain_response(response_generator)
        elif isinstance(stream, types.GeneratorType):
            blocks_generator = self._drain_response(stream)
        else:
            blocks_generator = self._drain_stream(stream)
        block = next(blocks_generator)
        while block:
            # hash = j.data.hash.md5_string(str(block) + str(self._vfile.id))
            # exists = self._block_model.find(md5=hash)
            # exists = self._block_model.get_by_name(md5=hash)
            # TODO: seems like there is a bug in bcdb that if you added the same id to a list multible times it will exxist only once
            # so we will disable block caching till we fix this
            if True:
                b = self._block_model.new()
                b.md5 = hash
                b.content = block
                b.size = len(block)
                b.epoch = j.data.time.epoch
                b.save()
                self._vfile.size_bytes += b.size
                self._vfile.blocks.append(b.id)
            else:
                self._vfile.size_bytes += exists[0].size
                self._vfile.blocks.append(exists[0].id)
            block = next(blocks_generator)
        self._vfile.save()

    def _save_plain(self, stream, append=True):
        if append:
            content = self._vfile.content
        else:
            content = ""
        if isinstance(stream, str):
            content = content + stream
        else:
            for line in stream.readlines():
                if isinstance(line, bytes):
                    line = line.decode()
                content = content + line + "\n"
        self._vfile.content = content
        self._vfile.size_bytes = len(self._vfile.content.encode())
        self._vfile.save()

    def read_stream_get(self):
        if self._vfile.content:
            ret = compat.BytesIO()
            ret.write(self._vfile.content.encode())
            ret.seek(0)
            return ret
        elif self._vfile.blocks:
            ret = compat.BytesIO()
            for block_id in self._vfile.blocks:
                ret.write(self._block_model.get(block_id).content)
            ret.seek(0)
            return ret
        else:
            return compat.BytesIO()

    def close(self):
        self._vfile.epoch = j.data.time.epoch
        self._vfile.content_type = mimetypes.guess_type(self._vfile.name)[0] or "text/plain"
        self._vfile.save()
