"""The ZipFile class provides convenience methods to work with zip archives"""

import sys
import os.path
import zipfile

from Jumpscale import j

JSBASE = j.baseclasses.object


class ZipFileFactory(j.baseclasses.object):
    READ = "r"
    WRITE = "w"
    APPEND = "a"
    __jslocation__ = "j.tools.zipfile"

    def get(self, path, mode=READ):
        return ZipFile(path, mode)


class ZipFile(j.baseclasses.object):
    """Handle zip files"""

    def __init__(self, path, mode=ZipFileFactory.READ):
        """Create a new ZipFile object

        @param path: Path to target zip file
        @type path: string
        @prarm mode: Action to perform on the zip file
        @type mode: ZipFileFactory Action
        """
        JSBASE.__init__(self)

        if not j.data.types.path.check(path):
            raise j.exceptions.Value("Provided string %s is not a valid path" % path)
        if mode is ZipFileFactory.READ:
            if not j.sal.fs.isFile(path):
                raise j.exceptions.Value("Provided path %s is not an existing file" % path)
            if not zipfile.is_zipfile(path):
                raise j.exceptions.Value("Provided path %s is not a valid zip archive" % path)
            self._zip = zipfile.ZipFile(path, "r")
            # TODO Make this optional?
            result = self._zip.testzip()
            if result is not None:
                raise j.exceptions.RuntimeError("Trying to open broken zipfile, first broken file is %s" % result)

        else:
            raise j.exceptions.Value("Invalid mode")

        self.path = path
        self.mode = mode

    def extract(self, destination_path, files=None, folder=None):
        """Extract all or some files from the archive to destination_path

        The files argument can be a list of names (relative from the root of
        the archive) to extract. If no file list is provided, all files
        contained in the archive will be extracted.

        @param destination_path: Extraction output folder
        @type destination_path: string
        @param files: Filenames to extract
        @type files: iterable
        @param folder: Folder to extract
        @type folder: string
        """
        if files and folder:
            raise j.exceptions.Value("Only files or folders can be provided, not both")

        if not files:
            files = self._zip.namelist()

        if folder:
            files = (f for f in files if os.path.normpath(f).startswith(folder))

        # normpath to strip occasional ./ etc
        for f in (os.path.normpath(_f) for _f in files if not _f.endswith("/")):
            dirname = os.path.dirname(f)
            basename = os.path.basename(f)

            outdir = j.sal.fs.joinPaths(destination_path, dirname)
            j.sal.fs.createDir(outdir)
            outfile_path = j.sal.fs.joinPaths(outdir, basename)

            # On Windows we get some \ vs / in path issues. Check whether the
            # provided filename works, if not, retry replacing \ with /, and use
            # this one if found.
            try:
                self._zip.getinfo(f)
            except KeyError:
                if not j.core.platformtype.myplatform.platform_is_windows:
                    raise
                f_ = f.replace("\\", "/")
                try:
                    self._zip.getinfo(f_)
                except KeyError:
                    pass
                else:
                    f = f_

            data = self._zip.read(f)
            # We need binary write
            self._log_info("Writing file %s" % outfile_path)
            fd = open(outfile_path, "wb")
            fd.write(data)
            fd.close()
            del data

    def close(self):
        """Close the backing zip file"""
        self._zip.close()
