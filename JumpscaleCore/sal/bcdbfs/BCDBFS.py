from Jumpscale import j
from unittest import TestCase
import re

JSBASE = j.baseclasses.object


class BCDBFS(j.baseclasses.object):
    """
    A sal for BCDB File System
    BCDB file system is a file system where everything is stored in bcdb
    """

    __jslocation__ = "j.sal.bcdbfs"

    def _init(self, bcdb_name="bcdbfs"):
        sql = j.clients.sqlitedb.client_get(namespace="bcdbfs")
        self._bcdb = j.data.bcdb.get(bcdb_name, storclient=sql)

        j.data.schema.add_from_path("%s/models_threebot" % j.data.bcdb._dirpath)

        self._file_model = self._bcdb.model_get_from_file("{}/models_threebot/FILE.py".format(self._bcdb._dirpath))
        self._dir_model = self._bcdb.model_get_from_file("{}/models_threebot/DIR.py".format(self._bcdb._dirpath))
        self.dir_create("/")

        """ def _is_filename_correct(self, filename):
            if filename.startswith("/") and len(filename) > 1:
                filename_to_test = filename[1:]
            else:
                filename_to_test = filename
            if not re.match(r"^[\w\-. ]+$", filename_to_test):
                return False
                # raise j.exceptions.Base("the filename %s is not a correct file name"%filename)
            return True

            def _is_directoryname_correct(self, dirname):
            if dirname.startswith("/") and len(dirname) > 1:
                dirname_to_test = dirname[1:]
            else:
                dirname_to_test = dirname
            if not re.match(r"^(\w+\.?)*\w+$", dirname_to_test):
                return False
                # raise j.exceptions.Base("the path %s is not a correct directory path"%dirname)
            return True """

    def _sanitize(self, path, isFile=None):
        """remove trailing slash.
        Preserve potential leading slash.
        """
        if path.endswith("/"):
            if isFile:
                raise j.exceptions.Base("filename path :%s should not end with a /" % path)
            if len(path) > 1:
                path = path[:-1]
        return j.sal.fs.pathClean(path)

    def exists(self, path):
        """
        checks is the path exists, it can be a directory or a file
        :param path: the path to be checked
        :return: bool
        """
        return self.dir_exists(self._sanitize(path)) or self.file_exists(self._sanitize(path))

    def is_dir(self, path):
        """
        checks if the path is a dir
        :param path: the path to checked
        :return: bool
        """
        return self.dir_exists(self._sanitize(path))

    def is_file(self, path):
        """
        checks if the path is a file
        :param path: the path to checked
        :return: bool
        """
        return self.file_exists(self._sanitize(path))

    #############################
    ######  DIR OPERATIONS ######
    #############################
    def dir_create(self, path):
        """
        create a directory
        :param path: full path of the directory
        :return: Directory object
        """
        if not self.dir_exists(self._sanitize(path, isFile=False)):
            return self._dir_model.create_empty_dir(self._sanitize(path, isFile=False))

    def dir_remove(self, path, recursive=True):
        """
        Remove directory
        :param path: directory path
        :param recursive: if true will perform recursive delete by deleting all sub directorie
        :return: None
        """
        dir = self._dir_model.get_by_name(name=self._sanitize(path, isFile=False))
        if not recursive and dir.dirs:
            raise j.exceptions.Base("this dir contains other dirs you must pass recursive = True")
        elif recursive:
            self._dir_model.delete_recursive(self._sanitize(path, isFile=False))

    def dir_exists(self, path):
        """
        checks if path is an existing directory
        :param path: path to be checked
        :return: bool
        """
        return self._dir_model.get_by_name(name=self._sanitize(path, isFile=False), die=False) is not None

    def dir_copy_from_local(self, path, dest, recursive=True):
        """
        copy directory from local file system to bcdb
        :param path: full path of the directory (the directory must exist on the local file system)
        :param dest: dest to copy the dir to on bcdbfs
        :param recursive: copy subdirs
        :return:
        """
        path = self._sanitize(path, isFile=False)
        source_files = j.sal.fs.listFilesInDir(path, True)
        for file in source_files:
            basename = j.sal.getBaseName(file)
            self.file_copy_from_local(file, j.sal.fs.joinPaths(path, basename))
        if recursive:
            source_dirs = j.sal.fs.listDirsInDir(path)
            for dir in source_dirs:
                self.dir_create(dir)
                basename = j.sal.fs.getBaseName(dir)
                self.dir_copy_from_local(dir, j.sal.fs.joinPaths(dest, basename))

    def dir_copy_from_bcdbfs(self, path, dest, recursive=True):
        """
        copy directory from a location in bcdbfs file system to another
        :param path: full path of the directory (the directory must exist in bcdbfs)
        :param dest: dest to copy the dir to on bcdbfs
        :param recursive: copy subdirs
        :return:
        """
        path = self._sanitize(path, isFile=False)
        if path == j.sal.fs.getParent(dest):
            raise j.exceptions.Base("{} can not copy directory into itself".format(path))
        dir_source = self._dir_model.get_by_name(name=path)
        # Make sure dest, exists coz sometimes we move empty directory into another one, so
        # in this case the emoty dir (dest) needs to created now otherwise they won't
        if not self.dir_exists(dest):
            self.dir_create(dest)
        source_files = dir_source.files
        for file_id in source_files:
            file = self._file_model.get(file_id)
            basename = j.sal.fs.getBaseName(file.name)
            self.file_copy_form_bcdbfs(file.name, j.sal.fs.joinPaths(dest, basename))
        if recursive:
            source_dirs = dir_source.dirs
            for dir_id in source_dirs:
                dir = self._dir_model.get(dir_id)
                self.dir_create(dir.name)
                basename = j.sal.fs.getBaseName(dir.name)
                self.dir_copy_from_bcdbfs(dir.name, j.sal.fs.joinPaths(dest, basename))

    def dir_copy(self, path, dest, recursive=True):
        """
        copies a dir from either local file system or from bcdbfs
        :param path: source path
        :param dest: destination
        :param recursive: copy subdirs
        :return:
        """
        path = self._sanitize(path, isFile=False)
        if j.sal.fs.exists(path):
            self.dir_copy_from_local(path, dest, recursive=recursive)
        else:
            self.dir_copy_from_bcdbfs(path, dest, recursive=recursive)

    #############################
    ###### FILE OPERATIONS ######
    #############################
    def file_create_empty(self, filename):
        """
        Creates empty file
        :param filename: full file path
        :return: file object
        """
        filename = self._sanitize(filename, isFile=True)
        if not self.file_exists(filename):
            return self._file_model.file_create_empty(filename)

    def file_write(self, filename, contents, append=True, create=True):
        """
        writes a file to bcdb
        :param path: the path to store the file
        :param content: content of the file to be written
        :param append: if True will append if the file already exists
        :param create: create new if true and the file doesn't exist
        :return: file object
        """
        return self._file_model.file_write(
            self._sanitize(filename, isFile=True), contents, append=append, create=create
        )

    def file_copy_from_local(self, path, dest):
        """
        copies file from local file system to bcdb
        :param path: path on local file system
        :param dest: destination on bcdbfs
        :return: file object
        """
        path = self._sanitize(path, isFile=True)
        if not j.sal.fs.exists(path):
            raise j.exceptions.Base("{} doesn't exist on local file system".format(path))

        with open(path, "rb") as f:
            self.file_write(dest, f, append=False, create=True)
        return

    def file_copy_form_bcdbfs(self, path, dest, overrrite=True):
        """
        copies file to another location in bcdbfs
        :param path: full path of the file
        :param dest: destination path
        :return: file object
        """
        path = self._sanitize(path, isFile=True)
        source_file = self._file_model.get_by_name(name=path)
        if self.is_dir(dest):
            dest = j.sal.fs.joinPaths(dest, j.sal.fs.getBaseName(path))
            if self.file_exists(dest) and overrrite:
                self.file_delete(dest)
        dest_file = self.file_create_empty(dest)
        if source_file.blocks:
            dest_file.blocks = source_file.blocks
        elif source_file.content:
            dest_file.content = source_file.content
        dest_file.size_bytes = source_file.size_bytes
        dest_file.epoch = source_file.epoch
        dest_file.content_type = source_file.content_type
        dest_file.save()
        return dest_file

    def get_epoch(self, path):
        path = self._sanitize(path)
        if j.sal.bcdbfs.is_dir(path):
            return self._dir_model.get_by_name(name=path).epoch
        return self._file_model.get_by_name(name=path).epoch

    def file_copy(self, path, dest, override=False):
        """
        copies file either from the local file system or from another location in bcdbfs
        :param path: full path to the file
        :param dest: destination path
        :return: file object
        """
        path = self._sanitize(path, isFile=True)
        # first check if path exists on the file system
        if self.exists(dest) and not override:
            return
        if j.sal.fs.exists(path):
            return self.file_copy_from_local(path, dest)
        else:
            return self.file_copy_form_bcdbfs(path, dest)

    def file_delete(self, path):
        """
        deletes a file
        :param path: a path of the file to be deleted
        :return: None
        """
        path = self._sanitize(path, isFile=True)
        self._file_model.file_delete(path)

    def file_exists(self, path):
        """
        checks if the path is existing file
        :param path: path for a file to be checked
        :return: bool
        """
        path = self._sanitize(path, isFile=True)
        return self._file_model.get_by_name(name=path, die=False) is not None

    def file_read(self, path):
        """
        reads a file
        :param path: the path to the file to read
        :return: Bytes stream
        """
        path = self._sanitize(path, isFile=True)
        return self._file_model.file_read(path)

    #############################
    ###### LIST OPERATIONS ######
    #############################

    def list_dirs(self, path="/"):
        """
        list dirs in path
        :param path: path to an existing directory
        :return: List[str] full paths
        """
        path = self._sanitize(path, isFile=False)
        dir_obj = self._dir_model.get_by_name(path)
        res = [self._dir_model.get(item).name for item in dir_obj.dirs]
        return res

    def list_files(self, path="/"):
        """
        list files in path
        :param path: path to an existing directory
        :return: List[str] full paths
        """
        path = self._sanitize(path, isFile=False)
        dir_obj = self._dir_model.get_by_name(path)
        res = [self._file_model.get(item).name for item in dir_obj.files]
        return res

    def list_files_and_dirs(self, path="/"):
        """
        list files and dirs in path
        :param path: path to an existing directory
        :return: List[str] full paths
        """
        path = self._sanitize(path)
        dirs = self.list_dirs(path)
        files = self.list_files(path)
        return dirs + files

    def _destroy(self):
        """
        VERY DANGEROUS: deletes everything in bcdbfs
        :return:
        """
        self._bcdb.reset()

    def search(self, text, location=""):
        """
        search in the content of files in a specific loaction
        :param text: text to search for
        :param location: location to search in, default: /
        :return: List[str] full paths
        """
        return [
            obj.name[len(location) + 1 : -3] for obj in self._file_model.search(text) if obj.name.startswith(location)
        ]

    def test(self):
        # add test for / fikes and folders
        cl = j.clients.sonic.get_client_bcdb()
        test_case = TestCase()
        cl.flush("bcdbfs")
        j.sal.bcdbfs.dir_create("/yolo/")
        assert j.sal.bcdbfs.dir_exists("/yolo")
        assert j.sal.bcdbfs.dir_exists("/yolo/")
        j.sal.bcdbfs.dir_remove("/yolo/")
        assert j.sal.bcdbfs.dir_exists("/yolo") == False
        assert j.sal.bcdbfs.dir_exists("/yolo/") == False
        with test_case.assertRaises(Exception) as cm:
            j.sal.bcdbfs.file_create_empty("/yolofile/")
        ex = cm.exception
        assert "filename path :%s should not end with a /" % "/yolofile/" in str(ex.args[0])
        j.sal.bcdbfs.file_create_empty("/yolofile")

        assert j.sal.bcdbfs.file_exists("/yolofile")
        with test_case.assertRaises(Exception) as cm:
            j.sal.bcdbfs.file_exists("/yolofile/")
        ex = cm.exception
        assert "filename path :%s should not end with a /" % "/yolofile/" in str(ex.args[0])

        with test_case.assertRaises(Exception) as cm:
            j.sal.bcdbfs.file_delete("/yolofile/")
        ex = cm.exception
        assert "filename path :%s should not end with a /" % "/yolofile/" in str(ex.args[0])

        j.sal.bcdbfs.file_delete("/yolofile")
        assert j.sal.bcdbfs.file_exists("/yolofile") == False

        j.sal.fs.createDir("/tmp/test_bcdbfs")
        j.sal.fs.writeFile("/tmp/test_bcdbfs/yolofile", "yolo content")
        with test_case.assertRaises(Exception) as cm:
            j.sal.bcdbfs.file_copy_from_local("/tmp/test_bcdbfs/yolofile", "/test/yolofile/")
        ex = cm.exception
        assert "filename path :%s should not end with a /" % "/test/yolofile/" in str(ex.args[0])
        j.sal.bcdbfs.file_copy_from_local("/tmp/test_bcdbfs/yolofile", "/test/yolofile")
        j.sal.fs.remove("/tmp/test_bcdbfs")
        assert j.sal.bcdbfs.file_read("/test/yolofile") == b"yolo content"
        j.sal.bcdbfs.file_delete("/test/yolofile")

        assert j.sal.bcdbfs.file_exists("/tmp/test_bcdbfs/yolofile") == False

        j.sal.bcdbfs.dir_create("/test")
        for i in range(5):
            j.sal.bcdbfs.dir_create("/test/dir_{}".format(i))
            j.sal.bcdbfs.file_create_empty("/test/test_{}".format(i))
            for k in range(5):
                j.sal.bcdbfs.file_create_empty(("/test/dir_{}/test_{}".format(i, k)))

        assert j.sal.bcdbfs.file_exists("/test/test_1")
        assert j.sal.bcdbfs.dir_exists("/test/dir_1")
        assert j.sal.bcdbfs.file_exists("/test/dir_1/test_4")

        assert j.sal.bcdbfs.is_dir("/test/dir_1")
        assert j.sal.bcdbfs.is_file("/test/dir_1/test_4")

        assert j.sal.bcdbfs.list_files("/test/dir_1") == [
            "/test/dir_1/test_0",
            "/test/dir_1/test_1",
            "/test/dir_1/test_2",
            "/test/dir_1/test_3",
            "/test/dir_1/test_4",
        ]
        assert j.sal.bcdbfs.list_dirs("/test") == [
            "/test/dir_0",
            "/test/dir_1",
            "/test/dir_2",
            "/test/dir_3",
            "/test/dir_4",
        ]
        assert j.sal.bcdbfs.list_files_and_dirs("/test") == [
            "/test/dir_0",
            "/test/dir_1",
            "/test/dir_2",
            "/test/dir_3",
            "/test/dir_4",
            "/test/test_0",
            "/test/test_1",
            "/test/test_2",
            "/test/test_3",
            "/test/test_4",
        ]

        j.sal.bcdbfs.file_copy_form_bcdbfs("/test/test_0", "/test/test_copied")
        j.sal.fs.createEmptyFile("/tmp/test_bcdbfs")

        j.sal.bcdbfs.file_copy_from_local("/tmp/test_bcdbfs", "/test/test_from_local")

        assert j.sal.bcdbfs.file_exists("/test/test_from_local")

        j.sal.bcdbfs.file_delete("/test/test_from_local")
        assert j.sal.bcdbfs.file_exists("/test/test_from_local") is False

        j.sal.fs.writeFile("/tmp/test_bcdbfs", "\ntest content\n\n\n")
        j.sal.bcdbfs.file_copy_from_local("/tmp/test_bcdbfs", "/test/test_with_content")
        assert j.sal.bcdbfs.file_read("/test/test_with_content") == b"\ntest content\n\n\n"

        j.sal.bcdbfs.dir_remove("/test")

        print("TESTS PASSED")
