import sys
import re
from Jumpscale import j
import os
import os.path
import hashlib
import fnmatch
import inspect  # needed for getPathOfRunningFunction
import shutil
import tempfile
import codecs
import pickle as pickle
import stat
from stat import ST_MTIME
import stat
from functools import wraps
import copy
from Jumpscale.sal.fs.SystemFSDecorators import (
    pathShorten,
    pathClean,
    pathDirClean,
    dirEqual,
    pathNormalize,
    cleanupString,
    path_check,
)

JSBASE = j.baseclasses.object
TESTTOOLS = j.baseclasses.testtools


class SystemFS(JSBASE, TESTTOOLS):

    __jslocation__ = "j.sal.fs"

    @path_check(fileFrom={"required", "replace", "exists", "file"}, to={"required"})
    def copyFile(self, fileFrom, to, createDirIfNeeded=False, overwriteFile=True):
        """Copy file

        Copies the file from C{fileFrom} to the file or directory C{to}.
        If C{to} is a directory, a file with the same basename as C{fileFrom} is
        created (or overwritten) in the directory specified.
        Permission bits are copied.

        @param fileFrom: Source file path name
        @type fileFrom: string
        @param to: Destination file or folder path name
        @type to: string

        @autocomplete

        """
        # Create target folder first, otherwise copy fails
        target_folder = os.path.dirname(to)
        if createDirIfNeeded:
            self.createDir(target_folder)
        if self.exists(to):
            if os.path.samefile(fileFrom, to):
                raise j.exceptions.Input("{src} and {dest} are the same file".format(src=fileFrom, dest=to))
            if overwriteFile is False:
                if os.path.samefile(to, target_folder):
                    destfilename = os.path.join(to, os.path.basename(fileFrom))
                    if self.exists(destfilename):
                        return
                else:
                    return
            elif self.isFile(to):
                # overwriting some open  files is frustrating and may not work
                # due to locking [delete/copy is a better strategy]
                self.remove(to)
        shutil.copy(fileFrom, to)
        self._log_debug("Copied file from %s to %s" % (fileFrom, to), _levelup=3)

    @path_check(source={"exists", "required", "replace", "file"}, destin={"required"})
    def moveFile(self, source, destin):
        """Move a  File from source path to destination path
        @param source: string (Source file path)
        @param destination: string (Destination path the file should be moved to )
        """
        self._log_debug("Move file from %s to %s" % (source, destin), _levelup=3)
        self._move(source, destin)

    def renameFile(self, filePath, new_name):
        """
        OBSOLETE
        """
        self._log_debug("WARNING: renameFIle should not be used", _levelup=3)
        return self._move(filePath, new_name)

    @path_check(path={"exists", "required", "replace", "dir"})
    def removeIrrelevantFiles(self, path, followSymlinks=True):
        """Will remove files having extensions: pyc, bak
        @param path: string (path to search in)
        """
        ext = ["pyc", "bak"]
        for path in self.listFilesInDir(path, recursive=True, followSymlinks=followSymlinks):
            if self.getFileExtension(path) in ext:
                self.remove(path)

    @path_check(path={"required"})
    def remove(self, path):
        """Remove a File
        @param path: string (File path required to be removed)
        """
        return j.core.tools.delete(path)

    @path_check(filename={"required", "replace"})
    def createEmptyFile(self, filename):
        """Create an empty file
        @param filename: string (file path name to be created)
        """
        self._log_debug("creating an empty file with name & path: %s" % filename, _levelup=3)
        open(filename, "w").close()
        self._log_debug("Empty file %s has been successfully created" % filename)

    @path_check(newdir={"required", "replace"})
    def createDir(self, newdir, unlink=False):
        """Create new Directory
        @param newdir: string (Directory path/name)
        if newdir was only given as a directory name, the new directory will be created on the default path,
        if newdir was given as a complete path with the directory name, the new directory will be created in the specified path
        """
        if newdir.find("file://") != -1:
            raise j.exceptions.RuntimeError("Cannot use file notation here")
        self._log_debug("Creating directory if not exists %s" % j.core.text.toStr(newdir), _levelup=3)
        if self.exists(newdir):
            if self.isLink(newdir) and unlink:
                self.unlink(newdir)

            if self.isDir(newdir):
                self._log_debug(
                    "Directory trying to create: [%s] already exists" % j.core.text.toStr(newdir), _levelup=3
                )
        else:
            head, tail = os.path.split(newdir)
            if head and (not self.exists(head) or not self.isDir(head)):
                self.createDir(head, unlink=False)
            if tail:
                os.mkdir(newdir)
                # try:
                #     os.mkdir(newdir)
                #     # print "mkdir:%s"%newdir
                # except OSError as e:
                #     if e.errno != os.errno.EEXIST:  # File exists
                #         raise

            self._log_debug("Created the directory [%s]" % j.core.text.toStr(newdir))

    def copyDirTree(
        self,
        src,
        dst,
        keepsymlinks=False,
        deletefirst=False,
        overwriteFiles=True,
        ignoredir=None,
        ignorefiles=None,
        rsync=True,
        ssh=False,
        sshport=22,
        recursive=True,
        rsyncdelete=True,
        createdir=False,
        showout=False,
        retry=5,
    ):
        """Recursively copy an entire directory tree rooted at src.
        The dst directory may already exist; if not,
        it will be created as well as missing parent directories
        @param src: string (source of directory tree to be copied)
        @param rsyncdelete will remove files on dest which are not on source (default) this works with the overwriteFiles to true otherwise it will not remove any files. Effective only when rsync=True
        @param recursive:  recursively look in all subdirs
        @param ignoredir: the following are always in, no need to specify ['.egg-info', '.dist-info', '__pycache__']
        @param ignorefiles: the following are always in, no need to specify: ["*.egg-info","*.pyc","*.bak"]
        @param rsync: bool. Use rsync for copying.
        @param ssh:  bool (copy to remote)
        @param sshport int (ssh port)
        @param createdir:   bool (when ssh creates parent directory)
        @param dst: string (path directory to be copied to...should not already exist)
        @param keepsymlinks: bool (True keeps symlinks instead of copying the content of the file)
        @param deletefirst: bool (Set to True if you want to erase symlinks/folders in the destination that also exist in the source, before copying.)
        @param overwriteFiles: if True will overwrite files, otherwise will not overwrite when destination exists
        """
        default_ignore_dir = [".egg-info", ".dist-info", "__pycache__"]
        if ignoredir is None:
            ignoredir = []
        if ignorefiles is None:
            ignorefiles = []
        for item in default_ignore_dir:
            if item not in ignoredir:
                ignoredir.append(item)
        default_ignorefiles = ["*.egg-info", "*.pyc", "*.bak"]
        for item in default_ignorefiles:
            if item not in ignorefiles:
                ignorefiles.append(item)

        if not rsync:
            if src.find("file://") != -1 or dst.find("file://") != -1:
                raise j.exceptions.RuntimeError("Cannot use file notation here")
            self._log_debug("Copy directory tree from %s to %s" % (src, dst), _levelup=3)
            if (src is None) or (dst is None):
                raise j.exceptions.Value(
                    "Not enough parameters passed in system.fs.copyDirTree to copy directory from %s to %s "
                    % (src, dst)
                )
            if self.isDir(src):
                names = os.listdir(src)

                if not self.exists(dst):
                    self.createDir(dst)

                errors = []
                for name in names:
                    # is only for the name
                    name2 = name

                    srcname = self.joinPaths(src, name)
                    dstname = self.joinPaths(dst, name2)

                    if self.isDir(srcname) and name in ignoredir:
                        continue
                    if self.isFile(srcname) and name in ignorefiles:
                        continue

                    if deletefirst and self.exists(dstname):
                        if self.isDir(dstname, False):
                            self.remove(dstname)
                        elif self.isLink(dstname):
                            self.unlink(dstname)

                    if self.isLink(srcname):
                        linkto = self.readLink(srcname)
                        if keepsymlinks:
                            self.symlink(linkto, dstname, overwriteFiles)
                            continue
                        else:
                            srcname = linkto
                    if self.isDir(srcname):
                        # print "1:%s %s"%(srcname,dstname)
                        self.copyDirTree(
                            srcname,
                            dstname,
                            keepsymlinks,
                            deletefirst,
                            overwriteFiles=overwriteFiles,
                            ignoredir=ignoredir,
                            ignorefiles=ignorefiles,
                            rsync=rsync,
                        )
                    if self.isFile(srcname):
                        # print "2:%s %s"%(srcname,dstname)
                        self.copyFile(srcname, dstname, createDirIfNeeded=False, overwriteFile=overwriteFiles)
            else:
                raise j.exceptions.RuntimeError("Source path %s in system.fs.copyDirTree is not a directory" % src)
        else:
            excl = " "
            for item in ignoredir:
                excl += "--exclude '*%s/' " % item

            for item in ignorefiles:
                excl += "--exclude '*%s' " % item

            dstpath2 = dst.split(":")[1] if ":" in dst else dst  # OTHERWISE CANNOT WORK FOR SSH

            dstpath = dst
            dstpath = self.pathClean(dstpath)

            src = self.pathClean(src)

            # ":" is there to make sure we support ssh
            if ":" not in src and j.sal.fs.isDir(src):
                if src[-1] != "/":
                    src += "/"
                if dstpath[-1] != "/":
                    dstpath += "/"

            cmd = "rsync --no-owner --no-group"
            if keepsymlinks:
                # -l is keep symlinks, -L follow
                cmd += " -rlt --partial %s" % excl
            else:
                cmd += " -rLt --partial %s" % excl
            if not recursive:
                cmd += ' --exclude "*/"'
            if not overwriteFiles:
                cmd += " --ignore-existing "
            if rsyncdelete and overwriteFiles:
                # --delete delete extraneous files from dest dirs
                # --delete-excluded also delete excluded files from dest dirs
                cmd += " --delete --delete-excluded "
            if ssh:
                cmd += " -e 'ssh -o StrictHostKeyChecking=no -p %s' " % sshport
                if createdir:
                    cmd += "--rsync-path='mkdir -p %s && rsync' " % self.getParent(dstpath2)
            else:
                self.createDir(self.getParent(dstpath))
            cmd += " '%s' '%s'" % (src, dst)
            cmd += " --verbose"
            j.core.tools.execute(
                cmd, showout=showout, die=True, retry=retry, errormsg="cannot rsync %s to %s" % (src, dstpath)
            )

    @path_check(path={"required", "replace", "exists", "dir"})
    def changeDir(self, path):
        """Changes Current Directory
        @param path: string (Directory path to be changed to)
        """
        self._log_debug("Changing directory to: %s" % path, _levelup=3)
        os.chdir(path)
        newcurrentPath = os.getcwd()
        self._log_debug("Directory successfully changed to %s" % path)
        return newcurrentPath

    @path_check(source={"exists", "required", "replace", "dir"})
    def moveDir(self, source, destin):
        """Move Directory from source to destination
        @param source: string (Source path where the directory should be removed from)
        @param destin: string (Destination path where the directory should be moved into)
        """
        self._log_debug("Moving directory from %s to %s" % (source, destin), _levelup=3)
        self._move(source, destin)
        self._log_debug("Directory is successfully moved from %s to %s" % (source, destin))

    def joinPaths(self, *args):
        """Join one or more path components.
        If any component is an absolute path, all previous components are thrown away, and joining continues.
        @param path1: string
        @param path2: string
        @param path3: string
        @param .... : string
        @rtype: Concatenation of path1, and optionally path2, etc...,
        with exactly one directory separator (os.sep) inserted between components, unless path2 is empty.
        """
        args = [j.core.text.toStr(x) for x in args]
        self._log_debug("Join paths %s" % (str(args)), _levelup=3)
        if args is None:
            raise j.exceptions.Value("Not enough parameters %s" % (str(args)))
        if os.sys.platform.startswith("win"):
            args2 = []
            for item in args:
                item = item.replace("/", "\\")
                while len(item) > 0 and item[0] == "\\":
                    item = item[1:]
                args2.append(item)
            args = args2
        return os.path.join(*args)

    @path_check(path={"required", "replace"})
    def getDirName(self, path, lastOnly=False, levelsUp=None):
        """
        Return a directory name from pathname path.
        @param path the path to find a directory within
        @param lastOnly means only the last part of the path which is a dir (overrides levelsUp to 0)
        @param levelsUp means, return the parent dir levelsUp levels up
         e.g. ...getDirName("/opt/qbase/bin/something/test.py", levelsUp=0) would return something
         e.g. ...getDirName("/opt/qbase/bin/something/test.py", levelsUp=1) would return bin
         e.g. ...getDirName("/opt/qbase/bin/something/test.py", levelsUp=10) would raise an error
        """
        self._log_debug("Get directory name of path: %s" % path, _levelup=3)
        dname = os.path.dirname(path)
        dname = dname.replace("/", os.sep)
        dname = dname.replace("//", os.sep)
        dname = dname.replace("\\", os.sep)
        if lastOnly:
            dname = dname.split(os.sep)[-1]
            return dname
        if levelsUp is not None:
            parts = dname.split(os.sep)
            if len(parts) - levelsUp > 0:
                return parts[len(parts) - levelsUp - 1]
            else:
                raise j.exceptions.RuntimeError(
                    "Cannot find part of dir %s levels up, path %s is not long enough" % (levelsUp, path)
                )
        return dname + os.sep if dname else dname

    @path_check(path={"required", "replace"})
    def getBaseName(self, path, removeExtension=False):
        """Return the base name of pathname path."""
        self._log_debug("Get basename for path: %s" % path, _levelup=3)
        name = os.path.basename(path.rstrip(os.path.sep))
        if removeExtension:
            if "." in name:
                name = ".".join(name.split(".")[:-1])
        return name

    # NO DECORATORS HERE
    def pathShorten(self, path):
        """
        Clean path (change /var/www/../lib to /var/lib). On Windows, if the
        path exists, the short path name is returned.

        @param path: Path to clean
        @type path: string
        @return: Cleaned (short) path
        @rtype: string
        """
        return pathShorten(path)

    # NO DECORATORS HERE
    def pathClean(self, path):
        """
        goal is to get a equal representation in / & \ in relation to os.sep
        """
        return pathClean(path)

    # NO DECORATORS HERE
    def pathDirClean(self, path):
        return pathDirClean(path)

    # NO DECORATORS HERE
    def dirEqual(self, path1, path2):
        return dirEqual(path)

    # NO DECORATORS HERE
    def pathNormalize(self, path):
        """
        paths are made absolute & made sure they are in line with os.sep
        @param path: path to normalize
        """
        return pathNormalize(path)

    def pathRemoveDirPart(self, path, toremove, removeTrailingSlash=False):
        """
        goal remove dirparts of a dirpath e,g, a basepath which is not needed
        will look for part to remove in full path but only full dirs
        """
        path = self.pathNormalize(path)
        toremove = self.pathNormalize(toremove)

        if self.pathClean(toremove) == self.pathClean(path):
            return ""
        path = self.pathClean(path)
        path = path.replace(self.pathDirClean(toremove), "")
        if removeTrailingSlash:
            if len(path) > 0 and path[0] == os.sep:
                path = path[1:]
        path = self.pathClean(path)
        return path

    def processPathForDoubleDots(self, path):
        """
        /root/somepath/.. would become /root
        /root/../somepath/ would become /somepath

        result will always be with / slashes
        """
        # print "processPathForDoubleDots:%s"%path
        path = self.pathClean(path)
        path = path.replace("\\", "/")
        result = []
        for item in path.split("/"):
            if item == "..":
                if result == []:
                    raise j.exceptions.RuntimeError("Cannot processPathForDoubleDots for paths with only ..")
                else:
                    result.pop()
            else:
                result.append(item)
        return "/".join(result)

    @path_check(path={"required", "replace"})
    def getParent(self, path):
        """
        Returns the parent of the path:
        /dir1/dir2/file_or_dir -> /dir1/dir2/
        /dir1/dir2/            -> /dir1/
        """
        parts = path.split(os.sep)
        if parts[-1] == "":
            parts = parts[:-1]
        parts = parts[:-1]
        if parts == [""]:
            return os.sep
        return os.sep.join(parts)

    def getParentWithDirname(self, path="", dirname=".git", die=False):
        """
        looks for parent which has $dirname in the parent dir, if found return
        if not found will return None or die

        Raises:
            RuntimeError -- if die

        Returns:
            string -- the path which has the dirname or None

        """
        if path == "":
            path = j.sal.fs.getcwd()

        # first check if there is no .jsconfig in parent dirs
        curdir = copy.copy(path)
        while curdir.strip() != "":
            if j.sal.fs.exists("%s/%s" % (curdir, dirname)):
                return curdir
            # look for parent
            curdir = j.sal.fs.getParent(curdir)
        if die:
            raise j.exceptions.Base("Could not find %s dir as parent of:'%s'" % (dirname, path))
        else:
            return None

    @path_check(path={"required", "replace"})
    def getFileExtension(self, path):
        ext = os.path.splitext(path)[1]
        return ext.strip(".")

    @path_check(path={"required", "replace"})
    def chown(self, path, user, group=None):
        from pwd import getpwnam
        from grp import getgrnam

        getpwnam(user)[2]
        uid = getpwnam(user).pw_uid
        if group is not None:
            gid = getgrnam(group).gr_gid
        else:
            gid = getpwnam(user).pw_gid
        os.chown(path, uid, gid)
        for root, dirs, files in os.walk(path):
            for ddir in dirs:
                path = os.path.join(root, ddir)
                try:
                    os.chown(path, uid, gid)
                except Exception as e:
                    if str(e).find("No such file or directory") == -1:
                        raise j.exceptions.RuntimeError("%s" % e)
            for file in files:
                path = os.path.join(root, file)
                try:
                    os.chown(path, uid, gid)
                except Exception as e:
                    if str(e).find("No such file or directory") == -1:
                        raise j.exceptions.RuntimeError("%s" % e)

    @path_check(path={"required", "replace", "exists"})
    def chmod(self, path, permissions):
        """
        @param permissions e.g. 0o660 (USE OCTAL !!!)
        """
        if permissions > 511 or permissions < 0:
            raise j.exceptions.Value("can't perform chmod, %s is not a valid mode" % oct(permissions))

        os.chmod(path, permissions)
        for root, dirs, files in os.walk(path):
            for ddir in dirs:
                path = os.path.join(root, ddir)
                try:
                    os.chmod(path, permissions)
                except Exception as e:
                    if str(e).find("No such file or directory") == -1:
                        raise j.exceptions.RuntimeError("%s" % e)

            for file in files:
                path = os.path.join(root, file)
                try:
                    os.chmod(path, permissions)
                except Exception as e:
                    if str(e).find("No such file or directory") == -1:
                        raise j.exceptions.RuntimeError("%s" % e)

    @path_check(path={"required"})
    def pathParse(self, path, baseDir="", existCheck=True, checkIsFile=False):
        """
        parse paths of form /root/tmp/33_adoc.doc into the path, priority which is numbers before _ at beginning of path
        also returns filename
        checks if path can be found, if not will fail
        when filename="" then is directory which has been parsed
        if basedir specified that part of path will be removed

        example:
        j.sal.fs.pathParse("/opt/qbase3/apps/specs/myspecs/definitions/cloud/datacenter.txt","/opt/qbase3/apps/specs/myspecs/",existCheck=False)
        @param path is existing path to a file
        @param baseDir, is the absolute part of the path not required
        @return list of dirpath,filename,extension,priority
             priority = 0 if not specified
        """
        # make sure only clean path is left and the filename is out
        if existCheck and not self.exists(path):
            raise j.exceptions.RuntimeError("Cannot find file %s when importing" % path)
        if checkIsFile and not self.isFile(path):
            raise j.exceptions.RuntimeError("Path %s should be a file (not e.g. a dir), error when importing" % path)
        extension = ""

        isDir = False
        if existCheck:
            isDir = self.isDir(path)

        if isDir:
            name = ""
            path = self.pathClean(path)
        else:
            name = self.getBaseName(path)
            path = self.pathClean(path)
            # make sure only clean path is left and the filename is out
            path = self.getDirName(path)
            # if it is a root directory getDirName will return //
            path = self.pathClean(path)
            # find extension
            regexToFindExt = "\.\w*$"
            if j.data.regex.match(regexToFindExt, name):
                extension = j.data.regex.findOne(regexToFindExt, name).replace(".", "")
                # remove extension from name
                name = j.data.regex.replace(
                    regexToFindExt, regexFindsubsetToReplace=regexToFindExt, replaceWith="", text=name
                )

        if baseDir != "":
            path = self.pathRemoveDirPart(path, baseDir)

        if name == "":
            dirOrFilename = self.getDirName(path, lastOnly=True)
        else:
            dirOrFilename = name

        if name == "" and dirOrFilename == "":
            # Here we are at a root level so instead of retruning an empty string we want to return the directory name
            dirOrFilename = self.pathClean(path)
        # check for priority
        regexToFindPriority = "^\d*_"
        if j.data.regex.match(regexToFindPriority, dirOrFilename):
            # found priority in path
            priority = j.data.regex.findOne(regexToFindPriority, dirOrFilename).replace("_", "")
            # remove priority from path
            name = j.data.regex.replace(
                regexToFindPriority, regexFindsubsetToReplace=regexToFindPriority, replaceWith="", text=name
            )
        else:
            priority = 0
        # for consistency reason path should always end with a /
        if len(path) > 0:
            if path[len(path) - 1] != "/":
                path += "/"
        else:
            path = "/"
        return path, name, extension, priority  # if name =="" then is dir

    def getcwd(self):
        """get current working directory
        @rtype: string (current working directory path)
        """
        self._log_debug("Get current working directory")
        return os.getcwd()

    @path_check(path={"required"})
    def readLink(self, path):
        """Works only for unix
        Return a string representing the path to which the symbolic link points.
        returns the source location (non relative)
        """
        while path[-1] == "/" or path[-1] == "\\":
            path = path[:-1]
        self._log_debug("Read link with path: %s" % path, _levelup=3)
        if j.core.platformtype.myplatform.platform_is_unix or j.core.platformtype.myplatform.platform_is_osx:
            res = os.readlink(path)
        elif j.core.platformtype.myplatform.platform_is_windows:
            raise j.exceptions.RuntimeError("Cannot readLink on windows")
        else:
            raise j.exceptions.Base("cant read link, dont understand platform")

        if res.startswith(".."):
            srcDir = self.getDirName(path)
            res = self.pathNormalize("%s%s" % (srcDir, res))
        elif self.getBaseName(res) == res:
            res = self.joinPaths(self.getParent(path), res)
        return res

    @path_check(path={"required", "replace", "exists"})
    def removeLinks(self, path):
        """
        find all links & remove
        """
        items = self._listAllInDir(path=path, recursive=True, followSymlinks=False, listSymlinks=True)
        items = [item for item in items[0] if self.isLink(item)]
        for item in items:
            self.unlink(item)

    def _listInDir(self, path, listSymlinks=True):
        """returns array with dirs & files in directory
        @param path: string (Directory path to list contents under)
        """
        names = os.listdir(path)
        if not listSymlinks:
            sym_links = self._list_sym_links(path)
            if sym_links:
                for link in sym_links:
                    if link in names:
                        names.remove(link)
        return names

    def _list_sym_links(self, path):
        sym_links = []
        for name in os.listdir(path):
            if name not in (os.curdir, os.pardir):
                full = os.path.join(path, name)
                if os.path.islink(full):
                    sym_links.append(name)
        return sym_links

    @path_check(path={"required", "replace", "exists", "dir"})
    def listFilesInDir(
        self,
        path,
        recursive=False,
        filter=None,
        minmtime=None,
        maxmtime=None,
        depth=None,
        case_sensitivity="os",
        exclude=[],
        followSymlinks=False,
        listSymlinks=False,
    ):
        """Retrieves list of files found in the specified directory
        @param path:       directory path to search in
        @type  path:       string
        @param recursive:  recursively look in all subdirs
        @type  recursive:  boolean
        @param filter:     unix-style wildcard (e.g. *.py) - this is not a regular expression
        @type  filter:     string
        @param minmtime:   if not None, only return files whose last modification time > minmtime (epoch in seconds)
        @type  minmtime:   integer
        @param maxmtime:   if not None, only return files whose last modification time < maxmtime (epoch in seconds)
        @Param depth: is levels deep wich we need to go
        @type  maxmtime:   integer
        @Param exclude: list of std filters if matches then exclude
        @rtype: list
        """
        if depth is not None:
            depth = int(depth)
        self._log_debug("List files in directory with path: %s" % path, _levelup=3)
        if depth == 0:
            depth = None
        # if depth is not None:
        #     depth+=1
        filesreturn, depth = self._listAllInDir(
            path,
            recursive,
            filter,
            minmtime,
            maxmtime,
            depth,
            type="f",
            case_sensitivity=case_sensitivity,
            exclude=exclude,
            followSymlinks=followSymlinks,
            listSymlinks=listSymlinks,
        )
        return filesreturn

    @path_check(path={"required", "replace", "exists", "dir"})
    def listFilesAndDirsInDir(
        self,
        path,
        recursive=True,
        filter=None,
        minmtime=None,
        maxmtime=None,
        depth=None,
        type="fd",
        followSymlinks=False,
        listSymlinks=False,
    ):
        """Retrieves list of files found in the specified directory
        @param path:       directory path to search in
        @type  path:       string
        @param recursive:  recursively look in all subdirs
        @type  recursive:  boolean
        @param filter:     unix-style wildcard (e.g. *.py) - this is not a regular expression
        @type  filter:     string
        @param minmtime:   if not None, only return files whose last modification time > minmtime (epoch in seconds)
        @type  minmtime:   integer
        @param maxmtime:   if not None, only return files whose last modification time < maxmtime (epoch in seconds)
        @Param depth: is levels deep wich we need to go
        @type  maxmtime:   integer
        @param type is string with f & d inside (f for when to find files, d for when to find dirs)
        @rtype: list
        """
        if depth is not None:
            depth = int(depth)
        self._log_debug("List files in directory with path: %s" % path, _levelup=3)
        if depth == 0:
            depth = None
        # if depth is not None:
        #     depth+=1
        filesreturn, _ = self._listAllInDir(
            path,
            recursive,
            filter,
            minmtime,
            maxmtime,
            depth,
            type=type,
            followSymlinks=followSymlinks,
            listSymlinks=listSymlinks,
        )
        return filesreturn

    def _listAllInDir(
        self,
        path,
        recursive,
        filter=None,
        minmtime=None,
        maxmtime=None,
        depth=None,
        type="df",
        case_sensitivity="os",
        exclude=[],
        followSymlinks=True,
        listSymlinks=True,
    ):
        """
        # There are 3 possible options for case-sensitivity for file names
        # 1. `os`: the same behavior as the OS
        # 2. `sensitive`: case-sensitive comparison
        # 3. `insensitive`: case-insensitive comparison
        """

        def filter_include(fullpath):
            include = False
            if (filter is None) or matcher(direntry, filter):
                if (minmtime is not None) or (maxmtime is not None):
                    mymtime = os.stat(fullpath)[ST_MTIME]
                    if (minmtime is None) or (mymtime > minmtime):
                        if (maxmtime is None) or (mymtime < maxmtime):
                            include = True
                else:
                    include = True
                if include:
                    if exclude != []:
                        for excludeItem in exclude:
                            if matcher(direntry, excludeItem):
                                include = False
            return include

        dircontent = self._listInDir(path, listSymlinks=listSymlinks)
        filesreturn = []

        if case_sensitivity.lower() == "sensitive":
            matcher = fnmatch.fnmatchcase
        elif case_sensitivity.lower() == "insensitive":

            def matcher(fname, pattern):
                return fnmatch.fnmatchcase(fname.lower(), pattern.lower())

        else:
            matcher = fnmatch.fnmatch

        for direntry in dircontent:
            fullpath = self.joinPaths(path, direntry)

            if self.isLinkAndBroken(fullpath):
                continue

            if followSymlinks:
                if self.isLink(fullpath):
                    fullpath = self.readLink(fullpath)

            if self.isFile(fullpath) and "f" in type:
                if filter_include(fullpath):
                    filesreturn.append(fullpath)
            elif self.isDir(fullpath):
                if "d" in type:
                    # if not(listSymlinks==False and self.isLink(fullpath)):
                    if filter_include(fullpath):
                        filesreturn.append(fullpath)
                if recursive:
                    newdepth = depth
                    if newdepth is not None and newdepth != 0:
                        newdepth = newdepth - 1
                    if newdepth is None or newdepth != 0:
                        exclmatch = False
                        if exclude != []:
                            for excludeItem in exclude:
                                if matcher(fullpath, excludeItem):
                                    exclmatch = True
                        if exclmatch is False:
                            if not (followSymlinks is False and self.isLink(fullpath, check_valid=True)):
                                r, _ = self._listAllInDir(
                                    fullpath,
                                    recursive,
                                    filter,
                                    minmtime,
                                    maxmtime,
                                    depth=newdepth,
                                    type=type,
                                    exclude=exclude,
                                    followSymlinks=followSymlinks,
                                    listSymlinks=listSymlinks,
                                )
                                if len(r) > 0:
                                    filesreturn.extend(r)
            # and followSymlinks==False and listSymlinks:
            elif self.isLink(fullpath) and followSymlinks == False and listSymlinks:
                filesreturn.append(fullpath)

        return filesreturn, depth

    def getPathOfRunningFunction(self, function):
        return inspect.getfile(function)

    def changeFileNames(
        self, toReplace, replaceWith, pathToSearchIn, recursive=True, filter=None, minmtime=None, maxmtime=None
    ):
        """
        @param toReplace e.g. {name}
        @param replace with e.g. "jumpscale"
        """
        if not toReplace:
            raise j.exceptions.Value("Can't change file names, toReplace can't be empty")
        if not replaceWith:
            raise j.exceptions.Value("Can't change file names, replaceWith can't be empty")
        paths = self.listFilesInDir(pathToSearchIn, recursive, filter, minmtime, maxmtime)
        for path in paths:
            dir_name = self.getDirName(path)
            file_name = self.getBaseName(path)
            new_file_name = file_name.replace(toReplace, replaceWith)
            if new_file_name != file_name:
                new_path = self.joinPaths(dir_name, new_file_name)
                self.renameFile(path, new_path)

    @path_check(path={"required", "replace"})
    def listDirsInDir(self, path, recursive=False, dirNameOnly=False, findDirectorySymlinks=True, followSymlinks=True):
        """ Retrieves list of directories found in the specified directory
        @param path: string represents directory path to search in
        @rtype: list
        """
        self._log_debug(
            "List directories in directory with path: %s, recursive = %s" % (path, str(recursive)), _levelup=3
        )

        items = self._listInDir(path)
        filesreturn = []
        for item in items:
            fullpath = os.path.join(path, item)
            if item.startswith("Icon"):
                continue
            if self.isDir(fullpath, findDirectorySymlinks):
                if dirNameOnly:
                    filesreturn.append(item)
                else:
                    filesreturn.append(fullpath)
            if recursive and self.isDir(fullpath, followSymlinks):
                if self.isLink(fullpath):
                    fullpath = self.readLink(fullpath)
                filesreturn.extend(
                    self.listDirsInDir(
                        fullpath,
                        recursive=recursive,
                        dirNameOnly=dirNameOnly,
                        findDirectorySymlinks=findDirectorySymlinks,
                        followSymlinks=followSymlinks,
                    )
                )
        return filesreturn

    @path_check(path={"required", "replace"})
    def listPyScriptsInDir(self, path, recursive=True, filter="*.py"):
        """ Retrieves list of python scripts (with extension .py) in the specified directory
        @param path: string represents the directory path to search in
        @rtype: list
        """
        result = []
        for file in self.listFilesInDir(path, recursive=recursive, filter=filter):
            if file.endswith(".py"):
                # filename = file.split(os.sep)[-1]
                # scriptname = filename.rsplit(".", 1)[0]
                result.append(file)
        return result

    @path_check(source={"required", "replace"}, destin={"required", "replace"})
    def _move(self, source, destin):
        """Main Move function
        @param source: string (If the specified source is a File....Calls moveFile function)
        (If the specified source is a Directory....Calls moveDir function)
        """
        if not self.exists(source):
            raise j.exceptions.IO("%s does not exist" % source)
        shutil.move(source, destin)

    @path_check(path={"required"})
    def exists(self, path, followlinks=True):
        """Check if the specified path exists
        @param path: string
        @rtype: boolean (True if path refers to an existing path)
        """
        if path is None:
            raise j.exceptions.Value("Path is not passed in system.fs.exists")

        found = False
        try:
            st = os.lstat(path)
            found = True
        except (OSError, AttributeError):
            pass
        if found and followlinks and stat.S_ISLNK(st.st_mode):
            self._log_debug("path %s exists" % str(path.encode("utf-8")), _levelup=3)
            relativelink = self.readLink(path)
            newpath = self.joinPaths(self.getParent(path), relativelink)
            return self.exists(newpath)
        if found:
            return True
        self._log_debug("path %s does not exist" % str(path.encode("utf-8")))
        return False

    @path_check(path={"required", "replace", "exists"}, target={"required", "replace"})
    def symlink(self, path, target, overwriteTarget=False):
        """Create a symbolic link
        @param path: source path desired to create a symbolic link for
        @param target: destination path required to create the symbolic link at
        @param overwriteTarget: boolean indicating whether target can be overwritten
        """
        self._log_debug("Getting symlink for path: %s to target %s" % (path, target), _levelup=3)

        if target[-1] == "/":
            target = target[:-1]

        if overwriteTarget and self.exists(target):
            if self.isLink(target):
                self.remove(target)
            elif self.isDir(target):
                self.remove(target)
            else:
                self.remove(target)

        if os.path.islink(target):
            self.remove(target)

        dir = self.getDirName(target)
        if not self.exists(dir):
            self.createDir(dir)

        if j.core.platformtype.myplatform.platform_is_unix or j.core.platformtype.myplatform.platform_is_osx:
            self._log_debug("Creating link from %s to %s" % (path, target))
            os.symlink(path, target)
        elif j.core.platformtype.myplatform.platform_is_windows:
            path = path.replace("+", ":")
            cmd = 'junction "%s" "%s"' % (
                self.pathNormalize(target).replace("\\", "/"),
                self.pathNormalize(path).replace("\\", "/"),
            )
            self._log_debug(cmd)
            j.sal.process.execute(cmd)

    @path_check(src={"required", "replace", "exists"}, dest={"required", "replace"})
    def symlinkFilesInDir(self, src, dest, delete=True, includeDirs=False, makeExecutable=False):
        if includeDirs:
            items = self.listFilesAndDirsInDir(src, recursive=False, followSymlinks=False, listSymlinks=False)
        else:
            items = self.listFilesInDir(src, recursive=False, followSymlinks=True, listSymlinks=True)
        for item in items:
            dest2 = "%s/%s" % (dest, self.getBaseName(item))
            dest2 = dest2.replace("//", "/")
            self._log_debug("link %s:%s" % (item, dest2))
            self.symlink(item, dest2, overwriteTarget=delete)
            if makeExecutable:
                # print("executable:%s" % dest2)
                self.chmod(dest2, 0o770)
                self.chmod(item, 0o770)

    @path_check(source={"required", "replace", "exists"}, destin={"required", "replace"})
    def hardlinkFile(self, source, destin):
        """Create a hard link pointing to source named destin. Availability: Unix.
        @param source: string
        @param destin: string
        @rtype: concatenation of dirname, and optionally linkname, etc.
        with exactly one directory separator (os.sep) inserted between components, unless path2 is empty
        """
        self._log_debug("Create a hard link pointing to %s named %s" % (source, destin), _levelup=3)
        if j.core.platformtype.myplatform.platform_is_unix or j.core.platformtype.myplatform.platform_is_osx:
            return os.link(source, destin)
        else:
            raise j.exceptions.RuntimeError("Cannot create a hard link on windows")

    @path_check(path={"required", "replace"})
    def checkDirParam(self, path):
        if path.strip() == "":
            raise j.exceptions.Value("path parameter cannot be empty.")
        path = self.pathNormalize(path)
        if path[-1] != "/":
            path = path + "/"
        return path

    @path_check(path={"required", "replace", "exists"})
    def isDir(self, path, followSoftlink=False):
        """Check if the specified Directory path exists
        @param path: string
        @param followSoftlink: boolean
        @rtype: boolean (True if directory exists)
        """
        if self.isLink(path):
            if not followSoftlink:
                return False
            path = self.readLink(path)
        return os.path.isdir(path)

    @path_check(path={"required", "replace", "exists", "dir"})
    def isEmptyDir(self, path):
        """Check if the specified directory path is empty
        @param path: string
        @rtype: boolean (True if directory is empty)
        """
        if self._listInDir(path) == []:
            self._log_debug("path %s is an empty directory" % path, _levelup=3)
            return True
        self._log_debug("path %s is not an empty directory" % path, _levelup=3)
        return False

    @path_check(path={"required", "replace", "exists"})
    def isFile(self, path, followSoftlink=True):
        """Check if the specified file exists for the given path
        @param path: string
        @param followSoftlink: boolean
        @rtype: boolean (True if file exists for the given path)
        """
        self._log_debug("isfile:%s" % path)
        if not followSoftlink and self.isLink(path):
            self._log_debug("path %s is a file" % path, _levelup=3)
            return True

        if os.path.isfile(path):
            self._log_debug("path %s is a file" % path, _levelup=3)
            return True

        self._log_debug("path %s is not a file" % path, _levelup=3)
        return False

    @path_check(path={"required", "replace", "exists", "file"})
    def isExecutable(self, path):
        statobj = self.statPath(path, follow_symlinks=False)
        return not (stat.S_IXUSR & statobj.st_mode == 0)

    def isLinkAndBroken(self, path, remove_if_broken=True):
        if os.path.islink(path):
            rpath = self.readLink(path)
            if not self.exists(rpath):
                if remove_if_broken:
                    j.sal.fs.remove(path)
                return True
        return False

    @path_check(path={"required", "replace"})
    def isLink(self, path, checkJunction=False, check_valid=False):
        """Check if the specified path is a link
        @param path: string
        @rtype: boolean (True if the specified path is a link)

        @PARAM check_valid if True, will remove link if the dest is not there and return False
        """
        if path[-1] == os.sep:
            path = path[:-1]

        if checkJunction and j.core.platformtype.myplatform.platform_is_windows:
            cmd = "junction %s" % path
            try:
                result = j.sal.process.execute(cmd)
            except Exception as e:
                raise j.exceptions.RuntimeError(
                    "Could not execute junction cmd, is junction installed? Cmd was %s." % cmd
                )
            if result[0] != 0:
                raise j.exceptions.RuntimeError(
                    "Could not execute junction cmd, is junction installed? Cmd was %s." % cmd
                )
            if result[1].lower().find("substitute name") != -1:
                return True
            else:
                return False

        if os.path.islink(path):
            if check_valid:
                if not os.path.exists(path):
                    self._log_debug("path %s is not a link and will be removed" % path, _levelup=3)
                    self.isLinkAndBroken(path)
                    return False
            return True
        self._log_debug("path %s is not a link" % path, _levelup=3)
        return False

    @path_check(path={"required", "replace", "dir", "exists"})
    def isMount(self, path):
        """Return true if pathname path is a mount point:
        A point in a file system where a different file system has been mounted.
        """
        self._log_debug("Check if path %s is a mount point" % path, _levelup=3)
        if path is None:
            raise j.exceptions.Value("Path is passed null in system.fs.isMount")
        return os.path.ismount(path)

    @path_check(path={"required", "replace", "exists"})
    def statPath(self, path, follow_symlinks=True):
        """Perform a stat() system call on the given path
        @rtype: object whose attributes correspond to the members of the stat structure
        """
        return os.stat(path, follow_symlinks=follow_symlinks)

    @path_check(dirname={"required", "replace", "exists", "dir"}, newname={"required", "replace"})
    def renameDir(self, dirname, newname, overwrite=False):
        """Rename Directory from dirname to newname
        @param dirname: string (Directory original name)
        @param newname: string (Directory new name to be changed to)
        """
        self._log_debug("Renaming directory %s to %s" % (dirname, newname), _levelup=3)
        if dirname == newname:
            return
        if overwrite and self.exists(newname):
            if self.isDir(newname):
                self.remove(newname)
            else:
                self.remove(newname)
        os.rename(dirname, newname)

    @path_check(filename={"required", "replace", "exists", "pureFile"})
    def unlinkFile(self, filename):
        """Remove the file path (only for files, not for symlinks)
        @param filename: File path to be removed
        """
        self._log_debug("Unlink file with path: %s" % filename, _levelup=3)
        os.unlink(filename)

    @path_check(filename={"required", "replace", "exists"})
    def unlink(self, filename):
        """Remove the given file if it's a file or a symlink

        @param filename: File path to be removed
        @type filename: string
        """
        self._log_debug("Unlink path: %s" % filename, _levelup=3)

        if j.core.platformtype.myplatform.platform_is_windows:
            cmd = "junction -d %s 2>&1 > null" % (filename)
            self._log_info(cmd)
            os.system(cmd)
        os.unlink(filename)

    @path_check(filename={"required", "replace", "exists", "file"})
    def readFile(self, filename, binary=False, encoding="utf-8"):
        """Read a file and get contents of that file
        @param filename: string (filename to open for reading )
        @rtype: string representing the file contents
        @param encoding utf-8 or ascii
        """
        self._log_debug("Read file: %s" % filename, _levelup=3)
        if binary:
            with open(filename, mode="rb") as fp:
                data = fp.read()
        else:
            with open(filename, encoding=encoding) as fp:
                data = fp.read()
        return data

    #
    # @path_check(filename={"required", "exists", "file"})
    # def fileGetUncommentedContents(self, filename):
    #     """Read a file and get uncommented contents of that file
    #     @param filename: string (filename to open for reading )
    #     @rtype: list of lines of uncommented file contents
    #     """
    #     self._log_debug('Opened file %s for reading' % filename)
    #     # self._log_debug('Reading file %s'% filename,9)
    #     with open(filename) as fp:
    #         data = fp.readlines()
    #         uncommented = list()
    #         for line in data:
    #             if not line.strip().startswith('#') and not line.startswith('\n'):
    #                 line = line.replace('\n', '')
    #                 uncommented.append(line)
    #         self._log_debug('File %s is closed after reading' % filename)
    #         return uncommented
    #
    # @path_check(filename={"required", "exists", "file"})
    # def fileGetTextContents(self, filename):
    #     """Read a UTF-8 file and get contents of that file. Takes care of the [BOM](http://en.wikipedia.org/wiki/Byte_order_mark)
    #     @param filename: string (filename to open for reading)
    #     @rtype: string representing the file contents
    #     """
    #     with open(filename, encoding='utf8') as f:  # enforce utf8 encoding
    #         s = f.read()
    #
    #         boms = [codecs.BOM_UTF8]
    #         for bom in boms:  # we can add more BOMs later:
    #             if s.startswith(bom.decode()):
    #                 s = s.replace(bom.decode(), '', 1)
    #                 break
    #         return s

    @path_check(paths={"required", "replace", "multiple"})
    def touch(self, paths):
        """
        can be single path or multiple (then list)
        """
        if j.data.types.list.check(paths):
            for item in paths:
                self.touch(item, overwrite=overwrite)
        path = paths
        self.createDir(self.getDirName(path))
        if not self.exists(path=path):
            self.writeFile(path, "")

    @path_check(filename={"required", "replace"})
    def writeFile(self, filename, contents, append=False):
        """
        Open a file and write file contents, close file afterwards
        @param contents: string (file contents to be written)
        """
        if contents is None:
            raise j.exceptions.Value("Passed None parameters in system.fs.writeFile")
        filename = j.core.tools.text_replace(filename)
        if append is False:
            fp = open(filename, "wb")
        else:
            fp = open(filename, "ab")
        self._log_debug("Write file %s" % filename, _levelup=3)
        if j.data.types.string.check(contents):
            fp.write(bytes(contents, "UTF-8"))
        else:
            fp.write(contents)
        # fp.write(contents)
        fp.close()

    @path_check(filename={"required", "replace", "exists", "file"})
    def fileSize(self, filename):
        """Get Filesize of file in bytes
        @param filename: the file u want to know the filesize of
        @return: int representing file size
        """
        return os.path.getsize(filename)

    @path_check(filelocation={"required", "replace"})
    def writeObjectToFile(self, filelocation, obj):
        """
        Write a object to a file(pickle format)
        @param filelocation: location of the file to which we write
        @param obj: object to pickle and write to a file
        """
        if not obj:
            raise j.exceptions.Value("You should provide a filelocation or a object as parameters")
        self._log_debug("Creating pickle and write it to file: %s" % filelocation, _levelup=3)
        try:
            pcl = pickle.dumps(obj)
        except Exception as e:
            raise Exception("Could not create pickle from the object \nError: %s" % (str(e)))
        self.writeFile(filelocation, pcl)
        if not self.exists(filelocation):
            raise Exception("File isn't written to the filesystem")

    @path_check(filelocation={"required", "replace", "exists", "file"})
    def readObjectFromFile(self, filelocation):
        """
        Read a object from a file(file contents in pickle format)
        @param filelocation: location of the file
        @return: object
        """
        self._log_debug("Opening file %s for reading" % filelocation, _levelup=3)
        contents = self.readFile(filelocation, binary=True)
        self._log_debug("creating object")
        return pickle.loads(contents)

    @path_check(filename={"required", "replace", "exists", "file"})
    def md5sum(self, filename):
        """Return the hex digest of a file without loading it all into memory
        @param filename: string (filename to get the hex digest of it) or list of files
        @rtype: md5 of the file
        """
        self._log_debug("Get the hex digest of file %s without loading it all into memory" % filename, _levelup=3)
        if not isinstance(filename, list):
            filename = [filename]
        digest = hashlib.md5()
        for filepath in filename:
            with open(filepath, "rb") as fh:
                while True:
                    buf = fh.read(4096)
                    if buf == b"":
                        break
                    digest.update(buf)
        return digest.hexdigest()

    @path_check(folder={"required", "replace", "exists", "dir"})
    def getFolderMD5sum(self, folder, ignore_empty_files=False):
        """Return the hex digest of a file without loading it all into memory
        @param folder: string (folder to get the hex digest of it)
        @param ignore_empty_files: Boolean (ignore empty files)
        @rtype: md5 of the directory
        """
        dir_hash = hashlib.md5()
        files = sorted(self.listFilesInDir(folder, recursive=True, followSymlinks=True, listSymlinks=True))
        for file in files:
            if ignore_empty_files:
                if self.fileSize(file) == 0:
                    continue
            with open(file, "rb") as fh:
                while True:
                    buf = fh.read(4096)
                    if buf == b"":
                        break
                    dir_hash.update(buf)
        return dir_hash.hexdigest()

    def getTmpDirPath(self, name="", create=True):
        """
        create a tmp dir name and makes sure the dir exists
        """
        if name:
            tmpdir = self.joinPaths(j.dirs.TMPDIR, name)
        else:
            tmpdir = self.joinPaths(j.dirs.TMPDIR, j.data.idgenerator.generateXCharID(10))
        if create is True:
            self.createDir(tmpdir)
        return tmpdir

    def getTmpFilePath(self, cygwin=False):
        """Generate a temp file path
        Located in temp dir of qbase
        @rtype: string representing the path of the temp file generated
        """
        tmpdir = j.dirs.TMPDIR + "/jumpscale/"
        j.sal.fs.createDir(tmpdir)
        fd, path = tempfile.mkstemp(dir=tmpdir)
        try:
            real_fd = os.fdopen(fd)
            real_fd.close()
        except (IOError, OSError):
            pass
        if cygwin:
            path = path.replace("\\", "/")
            path = path.replace("//", "/")
        return path

    def _file_path_tmp_get(self, ext="sh"):
        return j.core.tools._file_path_tmp_get(ext)

    @path_check(filename={"required", "replace", "exists", "file"})
    def isAsciiFile(self, filename, checksize=4096):
        # TODO: let's talk about checksize feature.
        try:
            with open(filename, encoding="ascii") as f:
                f.read()
                return True
        except UnicodeDecodeError:
            return False

    @path_check(filename={"required", "replace", "exists", "file"})
    def isBinaryFile(self, filename, checksize=4096):
        return not self.isAsciiFile(filename, checksize)

    def isAbsolute(self, path):
        path = path or ""
        return os.path.isabs(str(path))

    # THERE IS A tools.lock implementation we need to use that one
    # lock = staticmethod(lock)
    # lock_ = staticmethod(lock_)
    # islocked = staticmethod(islocked)
    # unlock = staticmethod(unlock)
    # unlock_ = staticmethod(unlock_)

    @path_check(filename={"replace"})
    def validateFilename(self, filename, platform=None):
        """Validate a filename for a given (or current) platform

        Check whether a given filename is valid on a given platform, or the
        current platform if no platform is specified.

        Rules
        =====
        Generic
        -------
        Zero-length filenames are not allowed

        Unix
        ----
        Filenames can contain any character except 0x00. We also disallow a
        forward slash ('/') in filenames.

        Filenames can be up to 255 characters long.

        Windows
        -------
        Filenames should not contain any character in the 0x00-0x1F range, '<',
        '>', ':', '"', '/', '\', '|', '?' or '*'. Names should not end with a
        dot ('.') or a space (' ').

        Several basenames are not allowed, including CON, PRN, AUX, CLOCK$,
        NUL, COM[1-9] and LPT[1-9].

        Filenames can be up to 255 characters long.

        Information sources
        ===================
        Restrictions are based on information found at these URLs:

         * http://en.wikipedia.org/wiki/Filename
         * http://msdn.microsoft.com/en-us/library/aa365247.aspx
         * http://www.boost.org/doc/libs/1_35_0/libs/filesystem/doc/portability_guide.htm
         * http://blogs.msdn.com/brian_dewey/archive/2004/01/19/60263.aspx

        @param filename: Filename to check
        @type filename: string
        @param platform: Platform to validate against
        @type platform: L{PlatformType}

        @returns: Whether the filename is valid on the given platform
        @rtype: bool
        """
        platform = platform or j.core.platformtype.myplatform

        if not filename:
            return False

        # When adding more restrictions to check_unix or check_windows, please
        # update the validateFilename documentation accordingly

        def check_unix(filename):
            if len(filename) > 255:
                return False

            if "\0" in filename or "/" in filename:
                return False

            return True

        def check_windows(filename):
            if len(filename) > 255:
                return False

            if os.path.splitext(filename)[0] in ("CON", "PRN", "AUX", "CLOCK$", "NUL"):
                return False

            if os.path.splitext(filename)[0] in ("COM%d" % i for i in range(1, 9)):
                return False

            if os.path.splitext(filename)[0] in ("LPT%d" % i for i in range(1, 9)):
                return False

            # ASCII characters 0x00 - 0x1F are invalid in a Windows filename
            # We loop from 0x00 to 0x20 (xrange is [a, b[), and check whether
            # the corresponding ASCII character (which we get through the chr(i)
            # function) is in the filename
            for c in range(0x00, 0x20):
                if chr(c) in filename:
                    return False

            for c in ("<", ">", ":", '"', "/", "\\", "|", "?", "*"):
                if c in filename:
                    return False

            if filename.endswith((" ", ".")):
                return False

            return True

        if platform.platform_is_windows:
            return check_windows(filename)

        if platform.platform_is_unix:
            return check_unix(filename)

        raise j.exceptions.NotImplemented("Filename validation on given platform not supported")

    @path_check(startDir={"required", "replace", "exists", "dir"})
    def find(self, startDir, fileregex):
        """Search for files or folders matching a given pattern
        example: find("*.pyc")
        @param fileregex: The regex pattern to match
        @type fileregex: string
        """
        result = []
        for root, dirs, files in os.walk(startDir, followlinks=True):
            for name in files:
                if fnmatch.fnmatch(name, fileregex):
                    result.append(os.path.join(root, name))
        return result

    def grep(self, fileregex, lineregex):
        """Search for lines matching a given regex in all files matching a regex

        @param fileregex: Files to search in
        @type fileregex: string
        @param lineregex: Regex pattern to search for in each file
        @type lineregex: string
        """
        import glob
        import re
        import os

        for filename in glob.glob(fileregex):
            if os.path.isfile(filename):
                f = open(filename, "r")
                for line in f:
                    if re.match(lineregex, line):
                        self._log_debug(("%s: %s" % (filename, line)))

    cleanupString = staticmethod(cleanupString)

    def constructDirPathFromArray(self, array):
        """
        Create a path using os specific seperators from a list being passed with directoy.

        @param array str: list of dirs in the path.
        """
        path = ""
        for item in array:
            path = path + os.sep + item
        path = path + os.sep
        if j.core.platformtype.myplatform.platform_is_unix or j.core.platformtype.myplatform.platform_is_osx:
            path = path.replace("//", "/")
            path = path.replace("//", "/")
        return path

    def constructFilePathFromArray(self, array):
        """
        Add file name  to dir path.

        @param array str: list including dir path then file name
        """
        path = self.constructDirPathFromArray(array)
        if path[-1] == "/":
            path = path[0:-1]
        return path

    def pathToUnicode(self, path):
        """
        Convert path to unicode. Use the local filesystem encoding. Will return
        path unmodified if path already is unicode.

        Use this to convert paths you received from the os module to unicode.

        @param path: path to convert to unicode
        @type path: basestring
        @return: unicode path
        @rtype: unicode
        """
        from Jumpscale.core.Dirs import Dirs

        return Dirs.pathToUnicode(path)

    @path_check(sourcepath={"required", "replace", "exists", "dir"}, destinationpath={"required"})
    def targzCompress(
        self,
        sourcepath,
        destinationpath,
        followlinks=False,
        destInTar="",
        pathRegexIncludes=[".[a-zA-Z0-9]*"],
        pathRegexExcludes=[],
        contentRegexIncludes=[],
        contentRegexExcludes=[],
        depths=[],
        extrafiles=[],
    ):
        """
        @param sourcepath: Source directory .
        @param destination: Destination filename.
        @param followlinks: do not tar the links, follow the link and add that file or content of directory to the tar
        @param pathRegexIncludes: / Excludes  match paths to array of regex expressions (array(strings))
        @param contentRegexIncludes: / Excludes match content of files to array of regex expressions (array(strings))
        @param depths: array of depth values e.g. only return depth 0 & 1 (would mean first dir depth and then 1 more deep) (array(int))
        @param destInTar when not specified the dirs, files under sourcedirpath will be added to root of
                  tar.gz with this param can put something in front e.g. /qbase3/ prefix to dest in tgz
        @param extrafiles is array of array [[source,destpath],[source,destpath],...]  adds extra files to tar
        (TAR-GZ-Archive *.tar.gz)
        """
        import os.path
        import tarfile

        self._log_debug("Compressing directory %s to %s" % (sourcepath, destinationpath), _levelup=3)
        if not self.exists(self.getDirName(destinationpath)):
            self.createDir(self.getDirName(destinationpath))
        t = tarfile.open(name=destinationpath, mode="w:gz")
        if not (
            followlinks
            or destInTar != ""
            or pathRegexIncludes != [".*"]
            or pathRegexExcludes != []
            or contentRegexIncludes != []
            or contentRegexExcludes != []
            or depths != []
        ):
            t.add(sourcepath, "/")
        else:

            def addToTar(params, path):
                tarfile = params["t"]
                destInTar = params["destintar"]
                destpath = self.joinPaths(destInTar, self.pathRemoveDirPart(path, sourcepath))
                if self.isLink(path) and followlinks:
                    path = self.readLink(path)
                self._log_debug("fs.tar: add file %s to tar" % path)
                # print "fstar: add file %s to tar" % path
                if not (j.core.platformtype.myplatform.platform_is_windows and j.sal.windows.checkFileToIgnore(path)):
                    tarfile.add(path, destpath)

            params = {}
            params["t"] = t
            params["destintar"] = destInTar
            j.sal.fswalker.walk(
                root=sourcepath,
                callback=addToTar,
                arg=params,
                recursive=True,
                includeFolders=False,
                pathRegexIncludes=pathRegexIncludes,
                pathRegexExcludes=pathRegexExcludes,
                contentRegexIncludes=contentRegexIncludes,
                contentRegexExcludes=contentRegexExcludes,
                depths=depths,
                followlinks=False,
            )

            if extrafiles != []:
                for extrafile in extrafiles:
                    source = extrafile[0]
                    destpath = extrafile[1]
                    t.add(source, self.joinPaths(destInTar, destpath))
        t.close()

    @path_check(sourceFile={"required", "replace", "exists", "file"}, destFile={"required", "replace"})
    def gzip(self, sourceFile, destFile):
        """
        Gzip source file into destination zip

        @param sourceFile str: path to file to be Gzipped.
        @param destFile str: path to  destination Gzip file.
        """
        import gzip

        f_in = open(sourceFile, "rb")
        f_out = gzip.open(destFile, "wb")
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()

    @path_check(sourceFile={"required", "replace", "exists", "file"}, destFile={"required", "replace"})
    def gunzip(self, sourceFile, destFile):
        """
        Gunzip gzip sourcefile into destination file

        @param sourceFile str: path to gzip file to be unzipped.
        @param destFile str: path to destination folder to unzip folder.
        """
        import gzip

        self.createDir(self.getDirName(destFile))
        f_in = gzip.open(sourceFile, "rb")
        f_out = open(destFile, "wb")
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()

    @path_check(sourceFile={"required", "replace", "exists", "file"}, destinationdir={"required", "replace"})
    def targzUncompress(self, sourceFile, destinationdir, removeDestinationdir=True):
        """
        compress dirname recursive
        @param sourceFile: file to uncompress
        @param destinationpath: path of to destiniation dir, sourcefile will end up uncompressed in destination dir
        """
        if removeDestinationdir:
            self.remove(destinationdir)
        if not self.exists(destinationdir):
            self.createDir(destinationdir)
        import tarfile

        # The tar of python does not create empty directories.. this causes
        # many problem while installing so we choose to use the linux tar here
        if j.core.platformtype.myplatform.platform_is_windows:
            tar = tarfile.open(sourceFile)
            tar.extractall(destinationdir)
            tar.close()
            # todo find better alternative for windows
        else:
            cmd = "tar xzf '%s' -C '%s'" % (sourceFile, destinationdir)
            j.sal.process.execute(cmd)

    def test(self, name=""):
        """
        it's run all tests
        kosmos 'j.sal.fs.test()'

        """
        self._test_run(name=name)

        print("TEST OK ALL PASSED")
