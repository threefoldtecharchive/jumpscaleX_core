import os
import os.path
from Jumpscale import j
import fnmatch

JSBASE = j.baseclasses.object


class SystemFSWalker(j.baseclasses.object):

    __jslocation__ = "j.sal.fswalker"

    @staticmethod
    def _checkDepth(path, depths, root=""):
        if depths == []:
            return True
        path = j.sal.fs.pathRemoveDirPart(path, root)
        for depth in depths:
            dname = os.path.dirname(path)
            split = dname.split(os.sep)
            split = [item for item in split if item != ""]
            # print split
            if depth == len(split):
                return True
        else:
            return False

    @staticmethod
    def _checkContent(path, contentRegexIncludes=[], contentRegexExcludes=[]):
        if not (contentRegexIncludes or contentRegexExcludes):
            return True

        if not j.sal.fs.isFile(path):
            # in this case the link doesn't link to a file so we can't read its content
            # add it in case of contentRegexExcludes is enabled
            return bool(contentRegexExcludes)

        content = j.sal.fs.readFile(path)
        if contentRegexIncludes and not j.data.regex.matchMultiple(patterns=contentRegexIncludes, text=content):
            return False

        if contentRegexExcludes and j.data.regex.matchMultiple(patterns=contentRegexExcludes, text=content):
            return False

        return True

    @staticmethod
    def _findhelper(arg, path):
        self._log_debug(path)
        arg.append(path)

    @staticmethod
    def find(
        root,
        recursive=True,
        includeFolders=False,
        pathRegexIncludes=[".*"],
        pathRegexExcludes=[".git"],
        contentRegexIncludes=[],
        contentRegexExcludes=[],
        depths=[],
        followlinks=True,
    ):
        listfiles = []
        SystemFSWalker.walk(
            root,
            SystemFSWalker._findhelper,
            listfiles,
            recursive,
            includeFolders,
            pathRegexIncludes,
            pathRegexExcludes,
            contentRegexIncludes,
            contentRegexExcludes,
            depths,
            followlinks=followlinks,
        )
        return listfiles

    @staticmethod
    def walk(
        root,
        callback,
        arg="",
        recursive=True,
        includeFolders=False,
        pathRegexIncludes=[".*"],
        pathRegexExcludes=[],
        contentRegexIncludes=[],
        contentRegexExcludes=[],
        depths=[],
        followlinks=True,
    ):
        """Walk through filesystem and execute a method per file

        Walk through all files and folders starting at C{root}, recursive by
        default, calling a given callback with a provided argument and file
        path for every file we could find.

        If C{includeFolders} is True, the callback will be called for every
        folder we found as well.

        Examples
        ========
        >>> def my_print(arg, path):
        ...     print arg, path
        ...
        >>> SystemFSWalker.walk('/foo', my_print, 'test:')
        test: /foo/file1
        test: /foo/file2
        test: /foo/file3
        test: /foo/bar/file4

        return False if you want recursion to stop (means don't go deeper)

        >>> def dirlister(arg, path):
        ...     print 'Found', path
        ...     arg.append(path)
        ...
        >>> paths = list()
        >>> SystemFSWalker.walk('/foo', dirlister, paths, recursive=False, includeFolders=True)
        /foo/file1
        /foo/file2
        /foo/file3
        /foo/bar
        >>> print paths
        ['/foo/file1', '/foo/file2', '/foo/file3', '/foo/bar']

        @param root: Filesystem root to crawl (string)
        @param callback: Callable to call for every file found, func(arg, path) (callable)
        @param arg: First argument to pass to callback
        @param recursive: Walk recursive or not (bool)
        @param includeFolders: Whether to call C{callable} for folders as well (bool)
        @param pathRegexIncludes / Excludes  match paths to array of regex expressions (array(strings))
        @param contentRegexIncludes / Excludes match content of files to array of regex expressions (array(strings))
        @param depths array of depth values e.g. only return depth 0 & 1 (would mean first dir depth and then 1 more deep) (array(int))

        """
        if not j.sal.fs.isDir(root):
            raise j.exceptions.Value("Root path for walk should be a folder")
        if recursive is False:
            depths = [0]
        # We want to work with full paths, even if a non-absolute path is
        # provided
        root = os.path.abspath(root)

        # print "ROOT OF WALKER:%s"%root
        # print "followlinks:%s"%followlinks
        j.sal.fswalker._walk(
            root,
            callback,
            arg,
            includeFolders,
            pathRegexIncludes,
            pathRegexExcludes,
            contentRegexIncludes,
            contentRegexExcludes,
            depths,
            followlinks=followlinks,
        )

        # #if recursive:
        # for dirpath, dirnames, filenames in os.walk(root,followlinks=followlinks):
        #     #Folders first
        #     if includeFolders:
        #         for dirname in dirnames:
        #             path = os.path.join(dirpath, dirname)
        #             if j.data.regex.matchMultiple(patterns=pathRegexIncludes,text=path) and \
        #                     not j.data.regex.matchMultiple(patterns=pathRegexExcludes,text=path):
        #                 if SystemFSWalker._checkDepth(path,depths,root) and \
        #                         SystemFSWalker._checkContent(path,contentRegexIncludes, contentRegexExcludes):
        #                     result=callback(arg, path)
        #     for filename in filenames:
        #         path = os.path.join(dirpath, filename)
        #         if j.data.regex.matchMultiple(patterns=pathRegexIncludes,text=path) and not j.data.regex.matchMultiple(patterns=pathRegexExcludes,text=path):
        #             if SystemFSWalker._checkDepth(path,depths,root) and SystemFSWalker._checkContent(path,contentRegexIncludes, contentRegexExcludes):
        #                 callback(arg, path)

    @staticmethod
    def _walk(
        path,
        callback,
        arg="",
        includeFolders=False,
        pathRegexIncludes=[".*"],
        pathRegexExcludes=[],
        contentRegexIncludes=[],
        contentRegexExcludes=[],
        depths=[],
        followlinks=True,
    ):

        for path2 in j.sal.fs.listFilesAndDirsInDir(path, followSymlinks=followlinks, listSymlinks=True):

            if j.sal.fs.isDir(path2, followlinks):
                if includeFolders:
                    result = True
                    if j.data.regex.matchMultiple(
                        patterns=pathRegexIncludes, text=path2
                    ) and not j.data.regex.matchMultiple(patterns=pathRegexExcludes, text=path2):
                        if SystemFSWalker._checkDepth(path2, depths, path) and SystemFSWalker._checkContent(
                            path2, contentRegexIncludes, contentRegexExcludes
                        ):
                            result = callback(arg, path2)
                    if result is False:
                        continue  # do not recurse go to next dir
                # recurse
                j.sal.fswalker._walk(
                    path2,
                    callback,
                    arg,
                    includeFolders,
                    pathRegexIncludes,
                    pathRegexExcludes,
                    contentRegexIncludes,
                    contentRegexExcludes,
                    depths,
                    followlinks,
                )

            elif j.sal.fs.isFile(path2, followlinks):
                if j.data.regex.matchMultiple(
                    patterns=pathRegexIncludes, text=path2
                ) and not j.data.regex.matchMultiple(patterns=pathRegexExcludes, text=path2):
                    if SystemFSWalker._checkDepth(path2, depths, path) and SystemFSWalker._checkContent(
                        path2, contentRegexIncludes, contentRegexExcludes
                    ):
                        callback(arg, path2)

    @staticmethod
    def walkFunctional(
        root,
        callbackFunctionFile=None,
        callbackFunctionDir=None,
        arg="",
        callbackForMatchDir=None,
        callbackForMatchFile=None,
        findDirectorySymlinks=True,
    ):
        """Walk through filesystem and execute a method per file and dirname

        Walk through all files and folders starting at C{root}, recursive by
        default, calling a given callback with a provided argument and file
        path for every file & dir we could find.

        To match the function use the callbackForMatch function which are separate for dir or file
        when it returns True the path will be further processed
        when None (function not given match will not be done)

        Examples
        ========
        >>> def my_print(path,arg):
        ...     print arg, path
        ...
        #if return False for callbackFunctionDir then recurse will not happen for that dir

        >>> def matchDirOrFile(path,arg):
        ...     return True #means will match all
        ...

        >>> SystemFSWalker.walkFunctional('/foo', my_print,my_print, 'test:',matchDirOrFile,matchDirOrFile)
        test: /foo/file1
        test: /foo/file2
        test: /foo/file3
        test: /foo/bar/file4

        @param root: Filesystem root to crawl (string)
        #TODO: complete

        """
        # We want to work with full paths, even if a non-absolute path is
        # provided
        root = os.path.abspath(root)

        if not j.sal.fs.isDir(root):
            raise j.exceptions.Value("Root path for walk should be a folder, {}".format(root))

        # print "ROOT OF WALKER:%s"%root
        SystemFSWalker._walkFunctional(
            root,
            callbackFunctionFile,
            callbackFunctionDir,
            arg,
            callbackForMatchDir,
            callbackForMatchFile,
            findDirectorySymlinks=findDirectorySymlinks,
        )

    @staticmethod
    def _walkFunctional(
        path,
        callbackFunctionFile=None,
        callbackFunctionDir=None,
        arg="",
        callbackForMatchDir=None,
        callbackForMatchFile=None,
        findDirectorySymlinks=True,
    ):

        paths = sorted(j.sal.fs.listFilesInDir(path, listSymlinks=True))
        for path2 in paths:
            if callbackForMatchFile is False:
                continue
            if callbackForMatchFile is None or callbackForMatchFile(path2, arg):
                # execute
                callbackFunctionFile(path2, arg)

        paths = sorted(j.sal.fs.listDirsInDir(path, findDirectorySymlinks=findDirectorySymlinks))
        for path2 in paths:
            # print "walker dirpath:%s"% path2
            if callbackForMatchDir is None or callbackForMatchDir(path2, arg):
                # recurse
                # print "walker matchdir:%s"% path2
                if callbackFunctionDir is None:
                    j.sal.fswalker._walkFunctional(
                        path2, callbackFunctionFile, callbackFunctionDir, arg, callbackForMatchDir, callbackForMatchFile
                    )
                else:
                    result = callbackFunctionDir(path2, arg)
                    if result:
                        # print "walker recurse:%s"% path2
                        j.sal.fswalker._walkFunctional(
                            path2,
                            callbackFunctionFile,
                            callbackFunctionDir,
                            arg,
                            callbackForMatchDir,
                            callbackForMatchFile,
                            findDirectorySymlinks=findDirectorySymlinks,
                        )

    @staticmethod
    def walkExtended(root, recurse=0, dirPattern="*", filePattern="*", followSoftLinks=True, dirs=True, files=True):
        """
        Extended Walk version: seperate dir and file pattern
        @param  root                : start directory to start the search.
        @type   root                : string
        @param  recurse             : search also in subdirectories.
        @type   recurse             : number
        @param  dirPattern          : search pattern to match directory names. Wildcards can be included.
        @type   dirPattern          : string
        @param  filePattern         : search pattern to match file names. Wildcards can be included.
        @type   filePattern         : string
        @param  followSoftLinks     : determine if links must be followed.
        @type   followSoftLinks     : boolean
        @param  dirs                : determine to return dir results.
        @type   dirs                : boolean
        @param  files               : determine to return file results.
        @type   files               : boolean
        @return                     : List of files and / or directories that match the search patterns.
        @rtype                      : list of strings
        General guidelines in the usage of the method be means of some examples come next. For the example in /tmp there is
        * a file test.rtt
        * and ./folder1/subfolder/subsubfolder/small_test/test.rtt
        To find the first test you can use
           j.sal.fswalker.walkExtended('/tmp/', dirPattern="*tmp*", filePattern="*.rtt")
        To find only the second one you could use
           j.sal.fswalker.walkExtended('tmp', recurse=0, dirPattern="*small_test*", filePattern="*.rtt", dirs=False)
        """
        result = []
        try:
            names = os.listdir(root)
        except os.error:
            return result  # TODO: P2 is this correct?

        dirPattern = dirPattern or "*"
        dirPatList = dirPattern.split(";")
        filePattern = filePattern or "*"
        filePatList = filePattern.split(";")

        for name in names:
            fullname = os.path.normpath(os.path.join(root, name))
            if j.sal.fs.isFile(fullname, followSoftLinks):
                fileOK = False
                dirOK = False
                for fPat in filePatList:
                    if fnmatch.fnmatch(name, fPat):
                        fileOK = True
                for dPat in dirPatList:
                    if fnmatch.fnmatch(os.path.dirname(fullname), dPat):
                        dirOK = True
                if fileOK and dirOK and files:
                    result.append(fullname)
            if j.sal.fs.isDir(fullname, followSoftLinks):
                for dPat in dirPatList:
                    if fnmatch.fnmatch(name, dPat) and dirs:
                        result.append(fullname)
            if recurse:
                result = result + j.sal.fswalker.walkExtended(
                    root=fullname,
                    recurse=recurse,
                    dirPattern=dirPattern,
                    filePattern=filePattern,
                    followSoftLinks=followSoftLinks,
                    dirs=dirs,
                    files=files,
                )

        return result
