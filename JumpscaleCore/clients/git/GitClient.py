from Jumpscale import j
import git
import copy


class GitClient(j.baseclasses.object):
    """
    Client of git services, has all git related operations like push, pull, ...
    """

    def __init__(self, baseDir, check_path=True):  # NOQA

        if baseDir is None or baseDir.strip() == "":
            raise j.exceptions.Base("basedir cannot be empty")

        baseDir_org = copy.copy(baseDir)

        j.baseclasses.object.__init__(self)

        self._repo = None
        if not j.sal.fs.exists(path=baseDir):
            raise j.exceptions.Input("git repo on %s not found." % baseDir_org)

        # split path to find parts
        baseDir = j.sal.fs.pathClean(baseDir)
        baseDir = baseDir.replace("\\", "/")  # NOQA
        baseDir = baseDir.rstrip("/")

        while ".git" not in j.sal.fs.listDirsInDir(
            baseDir, recursive=False, dirNameOnly=True, findDirectorySymlinks=True
        ):
            baseDir = j.sal.fs.getParent(baseDir)

            if baseDir == "/":
                break

        baseDir = baseDir.rstrip("/")

        if baseDir.strip() == "":
            raise j.exceptions.RuntimeError("could not find basepath for .git in %s" % baseDir_org)
        if check_path:
            if baseDir.find("/code/") == -1:
                raise j.exceptions.Input(
                    "jumpscale code management always requires path in form of $somewhere/code/$type/$account/$reponame"
                )

            base = baseDir.split("/code/", 1)[1]

            if not base.startswith("cockpit"):
                if base.count("/") != 2:
                    raise j.exceptions.Input(
                        "jumpscale code management always requires path in form of $somewhere/code/$type/$account/$reponame"
                    )
                self.type, self.account, self.name = base.split("/", 2)
            else:
                self.type, self.account, self.name = "github", "cockpit", "cockpit"
        else:
            self.type, self.account, self.name = "", "", j.sal.fs.getBaseName(baseDir)

        self.BASEDIR = baseDir

        # if len(self.repo.remotes) != 1:
        #     raise j.exceptions.Input("git repo on %s is corrupt could not find remote url" % baseDir)

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return self.__repr__()

    def setRemoteURL(self, url):
        """
        set the remote url of the repo
        """
        j.sal.process.executeWithoutPipe("cd %s;git remote set-url origin '%s'" % (self.BASEDIR, url))

    @property
    def remoteUrl(self):
        """
        get the remote url of the repo

        :raises Exception when ther eis no remote configuration for the repo, you will have to use setRemoteURL then
        """
        if len(self.repo.remotes) <= 0:
            # raise j.exceptions.Input(
            #    "There is not remote configured for this repository")
            self._log_warning("no remote repo configured (local repo?)")
            return ""  # XXX issue #60?
        return self.repo.remotes[0].url

    @property
    def branchName(self):
        """
        get the branch name of the repo
        """
        return self.repo.git.rev_parse("HEAD", abbrev_ref=True)

    @property
    def unc(self):
        """
        $gitcategory/$account/$repo/$branch
        """
        return "%s/%s/%s/%s" % (
            j.clients.git.rewriteGitRepoUrl(self.remoteUrl)[1],
            self.account,
            self.name,
            self.branchName,
        )

    @property
    def repo(self):
        """
        repo object
        """
        # Load git when we absolutly need it cause it does not work in gevent
        # mode
        if not self._repo:
            if not j.sal.fs.exists(self.BASEDIR):
                j.tools.executorLocal.execute("git config --global http.sslVerify false")
                self._clone()
            else:
                self._repo = git.Repo(self.BASEDIR)
        return self._repo

    def init(self, **kwargs):
        self.repo

    def getBranchOrTag(self):
        """
        get latest tag or branch

        :return: Python tuple, first parameter will indicate the type of the second parameter either tag or branch
        the second parameter will be the name of tag or branch
        """
        try:
            return "tag", self.repo.git.describe("--tags", "--exact-match")
        except BaseException:
            return "branch", self.repo.head.ref.name

    def switchBranch(self, branchName, create=True):  # NOQA
        """
        switch from the current branch to the selected branch

        :param branchName:(String) branch to switch to
        :param create:(Boolean) if True will create the destination branch if not exist
        """
        if create:
            import git

            try:
                self.repo.git.branch(branchName)
            except git.GitCommandError:
                # probably branch exists.
                print("was not able to create branch {}".format(branchName))
                pass
        self.repo.git.checkout(branchName)

    def checkFilesWaitingForCommit(self):
        """
        checks if there are modified, new, renamed, or deleted files which has not been yet committed,
        returns True if there are any, False otherwise
        """
        res = self.getModifiedFiles()
        if res["D"] != []:
            return True
        if res["M"] != []:
            return True
        if res["N"] != []:
            return True
        if res["R"] != []:
            return True
        return False

    def hasModifiedFiles(self):
        """
        :returns True if there is any file modified, new, renamed, or deleted and has not been yet committed,
        False otherwise
        """
        cmd = "cd %s;git status --porcelain" % self.BASEDIR
        rc, out, err = j.tools.executorLocal.execute(cmd, die=False)
        for item in out.split("\n"):
            item = item.strip()
            if item == "":
                continue
            return True
        return False

    def getModifiedFiles(self, collapse=False, ignore=[]):
        """
        get the list of modified files separated in dict of 4 lists
        N => New
        M => Modified
        R => Renamed
        D => Deleted

        :param collapse: (Boolean) if True, returns all files in one list
        :param ignore: (List) files to ignore
        """
        result = {}
        result["D"] = []  # Deleted
        result["N"] = []  # New
        result["M"] = []  # Modified
        result["R"] = []  # Renamed

        def checkignore(ignore, path):
            for item in ignore:
                if path.find(item) != -1:
                    return True
            return False

        cmd = "cd %s;git status --porcelain" % self.BASEDIR
        rc, out, err = j.tools.executorLocal.execute(cmd)
        # Organize files in lists
        for item in out.split("\n"):
            item = item.strip()
            if item == "":
                continue
            state, _, _file = item.partition(" ")
            if state == "??":
                if checkignore(ignore, _file):
                    continue
                result["N"].append(_file)
            if state in ["D", "N", "R", "M"]:
                if checkignore(ignore, _file):
                    continue
                if _file not in result[state]:
                    result[state].append(_file)

        # Organize files in lists
        for diff in self.repo.index.diff(None):
            # TODO: does not work, did not show my changes !!! *1
            if diff.a_blob is None:
                continue
            path = diff.a_blob.path
            if checkignore(ignore, path):
                continue
            if diff.deleted_file:
                if path not in result["D"]:
                    result["D"].append(path)
            elif diff.new_file:
                if path not in result["N"]:
                    result["N"].append(path)
            elif diff.renamed:
                if path not in result["R"]:
                    result["R"].append(path)
            else:
                if path not in result["M"]:
                    result["M"].append(path)

        if collapse:
            result = result["N"] + result["M"] + result["R"] + result["D"]
        return result

    def getUntrackedFiles(self):
        """
        :returns a list of untracked files
        """
        return self.repo.untracked_files

    def checkout(self, path):
        """
        checkout to the sent path
        """
        cmd = "cd %s;git checkout %s" % (self.BASEDIR, path)
        j.tools.executorLocal.execute(cmd)

    def addRemoveFiles(self):
        """
        add all untracked files
        """
        # cmd = 'cd %s;git add -A :/' % self.BASEDIR
        cmd = "cd %s;git add -A ." % self.BASEDIR
        j.tools.executorLocal.execute(cmd)

    def addFiles(self, files=[]):
        """
        add list of files to git index
        :param files: (List) files to be added
        """
        if files != []:
            self.repo.index.add(files)

    def removeFiles(self, files=[]):
        """
        remove list of files from git index

        :param files: (List) files to be removed
        """
        if files != []:
            self.repo.index.remove(files)

    def pull(self):
        """
        pull the current branch

        :raises Exception when there are files waiting for commit
        """
        if self.checkFilesWaitingForCommit():
            raise j.exceptions.Input(message="Cannot pull:%s, files waiting to commit" % self)
        self.repo.git.pull()

    def fetch(self):
        """
        fetch
        """
        self.repo.git.fetch()

    def commit(self, message="?", addremove=True):
        """
        commit the current repo state, or will return if no files to be committed

        :param message:(String) commit message
        :param addremove:(Boolean) if True, will add all untracked files to git
        """
        if addremove:
            self.addRemoveFiles()
        if self.hasModifiedFiles() is False:
            self._log_info("no need to commit, no changed files")
            return
        return self.repo.index.commit(message)

    def push(self, force=False):
        """
        push the local repo

        :param force:(Boolean) if True, will override the remote repo with the state of local repo. BE CAREFUL WHEN USING
        """
        if force:
            self.repo.git.push("-f")
        else:
            self.repo.git.push()

    def getChangedFiles(self, fromref="", toref="", fromepoch=None, toepoch=None, author=None, paths=[]):
        """
        list all changed files since ref & epoch (use both)

        @param fromref = commit ref to start from
        @param toref = commit ref to end at
        @param author if limited to author
        @param path if only list changed files in paths
        @param fromepoch = starting epoch
        @param toepoch = ending epoch
        @return
        """
        commits = self.getCommitRefs(
            fromref=fromref, toref=toref, fromepoch=fromepoch, toepoch=toepoch, author=author, paths=paths, files=True
        )
        files = [f for commit in commits for f in commit[3]]
        return list(set(files))

    def getCommitRefs(self, fromref="", toref="", fromepoch=None, toepoch=None, author=None, paths=None, files=False):
        """
        @return [[$epoch, $ref, $author]] if no files (default)
        @return [[$epoch, $ref, $author, $files]] if files
        @param files = True means will list the files
        """
        kwargs = {"branches": [self.branchName]}
        if fromepoch:
            kwargs["max-age"] = fromepoch
        if toepoch:
            kwargs["min-age"] = toepoch
        if fromref or toref:
            if fromref and not toref:
                kwargs["rev"] = "%s" % fromref
            elif fromref and toref:
                kwargs["rev"] = "%s..%s" % (fromref, toref)
        if author:
            kwargs["author"] = author
        commits = list()
        for commit in list(self.repo.iter_commits(paths=paths, **kwargs)):
            if files:
                commits.append(
                    (commit.authored_date, commit.hexsha, commit.author.name, list(commit.stats.files.keys()))
                )
            else:
                commits.append((commit.authored_date, commit.hexsha, commit.author.name))
        return commits

    def getFileChanges(self, path):
        """
        @return lines which got changed
        format:
        {'line': [{'commit sha': '', 'author': 'author'}]}
        """
        # TODO *3 limit to max number?
        diffs = dict()
        blame = self.repo.blame(self.branchName, path)
        for commit, lines in blame:
            for line in lines:
                diffs[line] = list() if line not in diffs else diffs[line]
                diffs[line].append({"author": commit.author.name, "commit": commit.hexsha})

        return diffs

    def patchGitignore(self):
        gitignore = """
            # Byte-compiled / optimized / DLL files
            __pycache__/
            *.py[cod]
            
            # C extensions
            *.so
            
            # Distribution / packaging
            .Python
            develop-eggs/
            eggs/
            sdist/
            var/
            *.egg-info/
            .installed.cfg
            *.egg
            
            # Installer logs
            pip-log.txt
            pip-delete-this-directory.txt
            
            # Unit test / coverage reports
            .tox/
            .coverage
            .cache
            nosetests.xml
            coverage.xml
            
            # Translations
            *.mo
            
            # Mr Developer
            .mr.developer.cfg
            .project
            .pydevproject
            
            # Rope
            .ropeproject
            
            # Django stuff:
            *.log
            *.pot
            
            # Sphinx documentation
            docs/_build/
            """
        gitignore = j.core.tools.text_strip(gitignore)
        ignorefilepath = j.sal.fs.joinPaths(self.BASEDIR, ".gitignore")
        if not j.sal.fs.exists(ignorefilepath):
            j.sal.fs.writeFile(ignorefilepath, gitignore)
        else:
            lines = gitignore.splitlines()
            inn = j.sal.fs.readFile(ignorefilepath)
            lines = inn.splitlines()
            linesout = []
            for line in lines:
                if line.strip():
                    linesout.append(line)
            for line in lines:
                if line not in lines and line.strip():
                    linesout.append(line)
            out = "\n".join(linesout)
            if out.strip() != inn.strip():
                j.sal.fs.writeFile(ignorefilepath, out)

    def describe(self):
        """
        this method get latest tag or branch
        """
        try:
            cmd = "cd {path}; git describe --tags".format(path=self.BASEDIR)
            return "tag", j.tools.executorLocal.execute(cmd)[1]
        except BaseException:
            return "branch", self.repo.head.ref.name

    def getConfig(self, field):
        """
        returns value of provided field name
        returns empty string if not found

        :param fields: field name of the config to search for
        :return: string value of the field name
        """
        cmd = "cd %s; git config %s" % (self.BASEDIR, field)
        rc, output, _ = j.tools.executorLocal.execute(cmd, die=False)
        if rc != 0:
            return ""

        return output.strip()

    def setConfig(self, field, value, local=True, die=True):
        """
        Sets provided field with value to the git config

        :param field: field name to be set
        :param value: value of field to be set
        :param local: Set value as local config, set to false for global config
        :param die: raise exception on error
        """
        flags = ""
        if not local:
            flags += "--global "

        cmd = "cd %s; git config %s %s %s" % (self.BASEDIR, flags, field, value)
        j.tools.executorLocal.execute(cmd, die=die)

    def unsetConfig(self, field, local=True, die=True):
        """
        Removes/unsets config field

        :param field: fieldname to remove
        :param local: remove from local config, set to false to remove from global config
        :param die: raise exception on error
        """
        flags = ""
        if not local:
            flags += "--global "

        cmd = "cd %s; git config --unset %s %s" % (self.BASEDIR, flags, field)
        j.tools.executorLocal.execute(cmd, die=die)
