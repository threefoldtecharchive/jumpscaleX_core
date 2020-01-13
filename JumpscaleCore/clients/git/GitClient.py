from Jumpscale import j
import git
import copy


class GitClient(j.baseclasses.object):
    """
    Client of git services, has all git related operations like push, pull, ...
    """

    def __init__(self, baseDir, check_path=True):
        """

        :param baseDir: the dir of the gitclient
        :param check_path: will find /code/ and put some extra arguments
        """

        self._3git_config = None
        self._ignore_items = None

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

        self.path = baseDir

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
        j.sal.process.executeWithoutPipe("cd %s;git remote set-url origin '%s'" % (self.path, url))

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
            if not j.sal.fs.exists(self.path):
                j.tools.executor.local.execute("git config --global http.sslVerify false")
                self._clone()
            else:
                self._repo = git.Repo(self.path)
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

    def hasModifiedFiles(self, path=None):
        """
        :returns True if there is any file modified, new, renamed, or deleted and has not been yet committed,
        False otherwise
        """
        if not path:
            path = self.path
        cmd = "cd %s;git status --porcelain" % path
        rc, out, err = j.tools.executor.local.execute(cmd, die=False)
        for item in out.split("\n"):
            item = item.strip()
            if item == "":
                continue
            return True
        return False

    @property
    def _config_3git_path(self):
        return self.path + "/.3gitconfig.toml"

    @property
    def config_3git(self):
        if not self._3git_config:
            if j.sal.fs.exists(self._config_3git_path):
                self._3git_config = j.data.serializers.toml.load(self._config_3git_path)
            else:
                self._3git_config = {}
        return self._3git_config

    def config_3git_save(self):
        j.data.serializers.toml.dump(self._config_3git_path, self._3git_config)

    def config_3git_get(self, name, default=""):
        if not name in self.config_3git:
            self.config_3git[name] = default
            self.config_3git_save()
        return self.config_3git[name]

    def config_3git_set(self, name, val=""):
        v = self.config_3git_get(name=name)
        if v == "" or v != val:
            self.config_3git[name] = val
            self.config_3git_save()

    def logChanges(self, from_revision=None, all=False, untracked=True, path=None):
        """

        :param from_revision:
        :param all: don't check previous state, list all
        :param untracked:  also add the untracked files
        :return:  (lastrevision,changes)

        this is the method to use to e.g. find documents ready to process since last processing step,
        just need to remember the revision from last successful run

        """
        revision = None
        if not from_revision and all is False:
            from_revision = self.config_3git_get("revision_last_processed")
        path = path or self.path
        if from_revision:
            cmd = f"cd {path};git --no-pager log {from_revision}..HEAD --name-status --oneline --reverse {path}"
        else:
            cmd = f"cd {path};git --no-pager log --name-status --oneline --reverse {path}"

        rc, out, err = j.tools.executor.local.execute(cmd)
        # Organize files in lists
        result = []
        to_delete = []
        for item in out.split("\n"):
            item = item.strip()
            if item == "":
                continue

            if "\t" in item:
                pre, post, = item.split("\t", 1)
            else:
                pre, post, = item.split(" ", 1)
            if len(pre) > 6:
                revision = pre
                msg = post
            else:
                state = pre[0]
                _file = post
                if state in ["N", "M", "A"]:
                    if _file not in result:
                        result.append(_file)
                        self._log_info(f"File {_file} created")
                elif state.startswith("R"):
                    from_, to_ = post.split("\t")
                    if from_ != to_:
                        to_delete.append(from_)
                    if from_ in result:
                        result.pop(result.index(from_))
                    if to_ not in result:
                        result.append(to_)
                    self._log_info(f"File {_file} renamed")
                elif state == "D":
                    # delete
                    if _file in result:
                        result.pop(result.index(_file))
                        self._log_info(f"File {_file} deleted")
                        to_delete.append(_file)

                # else:
                #     print("state", state, item)
                #     # TODO: handle other states codes
                #     j.shell()
                #     w
        if untracked:
            for item in self.getModifiedFiles(collapse=True, path=path):
                if item not in result:
                    result.append(item)

        if not revision:
            revision = from_revision

        return (revision, result, to_delete)

    def logChangesRevisionSet(self, revision):
        """
        will mark in repo the last revision which has been processed so we don't process previously committed files
        :return:
        """
        self.config_3git_set("revision_last_processed", revision)

    def getModifiedFiles(self, collapse=False, ignore=[], path=None):
        """
        get the list of modified files separated in dict of 4 lists
        N => New
        M => Modified
        R => Renamed
        D => Deleted

        :param collapse: (Boolean) if True, returns all files in one list
        :param ignore: (List) files to ignore
        """
        if not path:
            path = self.path
        if not path.startswith("/"):
            path = "%s/%s" % (self.path, path)  # means is relative

        assert j.sal.fs.exists(path)

        result = {}
        result["D"] = []  # Deleted
        result["N"] = []  # New
        result["A"] = []  # Added
        result["M"] = []  # Modified
        result["R"] = []  # Renamed

        def checkignore(ignore, path):
            for item in ignore:
                if path.find(item) != -1:
                    return True
            return False

        cmd = "cd %s;git status --porcelain %s" % (path, path)
        rc, out, err = j.tools.executor.local.execute(cmd)
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
            # handle other states
            if state in ["D", "N", "R", "M", "A", "AD", "AA", "DD"]:
                if checkignore(ignore, _file):
                    continue
                if _file not in result[state[-1]]:
                    result[state[-1]].append(_file)

        # IS DUPLICATION WITH ABOVE
        # # Organize files in lists
        # for diff in self.repo.index.diff(None):
        #     # TODO: does not work, did not show my changes !!! *1
        #     if diff.a_blob is None:
        #         continue
        #     path = diff.a_blob.path
        #     if checkignore(ignore, path):
        #         continue
        #     if diff.deleted_file:
        #         if path not in result["D"]:
        #             result["D"].append(path)
        #     elif diff.new_file:
        #         if path not in result["N"]:
        #             result["N"].append(path)
        #     elif diff.renamed:
        #         if path not in result["R"]:
        #             result["R"].append(path)
        #     else:
        #         if path not in result["M"]:
        #             result["M"].append(path)

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
        cmd = "cd %s;git checkout %s" % (self.path, path)
        j.tools.executor.local.execute(cmd)

    def addRemoveFiles(self):
        """
        add all untracked files
        """
        # cmd = 'cd %s;git add -A :/' % self.path
        cmd = "cd %s;git add -A ." % self.path
        j.tools.executor.local.execute(cmd)

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

    def file_changes_get(self, path):
        """
        @return lines which got changed (since last commit)
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

    @property
    def gitignore_items(self):
        """
        return list of items in gitignore
        :return:
        """
        if not self._ignore_items:
            self._ignore_items = []
            ignorefilepath = j.sal.fs.joinPaths(self.path, ".gitignore")
            if not j.sal.fs.exists(ignorefilepath):
                self.gitignore_patch()
            inn = j.sal.fs.readFile(ignorefilepath)
            lines_in = inn.splitlines()
            for item in lines_in:
                item = item.strip()
                if item:
                    if item not in self._ignore_items:
                        self._ignore_items.append(item)
        return self._ignore_items

    # def gitignoreCheck(self, path):
    #     """
    #     :param path:
    #     :return: True if in ignore list
    #     """
    #     if path.startswith("/"):
    #         # means need to remove the basepath and only if its in the current basepath
    #         if not path.startswith(self.path):
    #             raise j.exceptions.Input("path needs to be in git repo:%s" % path)
    #         j.shell()
    #     for item in self.gitignore_items:
    #         if item.endswith("/"):
    #             # is dir check
    #             if path.startswith(item):
    #                 return True
    #         elif item.startswith("*"):
    #             item2 = item.replace("*", "")
    #             if path.endswith(item2):
    #                 return True
    #         elif item.endswith("*"):
    #             item2 = item.replace("*", "")
    #             if path.startswith(item2):
    #                 return True

    def gitignore_patch(self):
        gitignore = """

            logs
            *.log
            npm-debug.log*
            yarn-debug.log*
            yarn-error.log*
            pids
            *.pid
            *.seed
            *.pid.lock
            lib-cov
            coverage
            .nyc_output
            .grunt
            bower_components
            .lock-wscript
            build/Release
            node_modules/
            jspm_packages/
            typings/
            .npm
            .eslintcache
            .node_repl_history
            *.tgz
            .yarn-integrity
            .env
            .next

            __pycache__/
            *.py[cod]
            *.so

            .Python
            develop-eggs/
            eggs/
            sdist/
            var/
            *.egg-info/
            .installed.cfg
            *.egg

            pip-log.txt
            pip-delete-this-directory.txt

            .tox/
            .coverage
            .cache
            nosetests.xml
            coverage.xml

            # Translations
            *.mo

            .mr.developer.cfg
            .project
            .pydevproject
            .ropeproject
            *.pot

            docs/_build/
            errors.md

            """

        gitignore = j.core.tools.text_strip(gitignore)
        ignorefilepath = j.sal.fs.joinPaths(self.path, ".gitignore")
        change = False
        if not j.sal.fs.exists(ignorefilepath):
            j.sal.fs.writeFile(ignorefilepath, gitignore)
        else:
            lines = gitignore.splitlines()
            inn = j.sal.fs.readFile(ignorefilepath)
            lines_in = inn.splitlines()
            linesout = []
            for line in lines:
                line = line.strip()
                if line:
                    if line not in linesout:
                        linesout.append(line)
                        if line not in lines_in:
                            change = True
            if change:
                out = "\n".join(linesout)
                j.sal.fs.writeFile(ignorefilepath, out)

    def describe(self):
        """
        this method get latest tag or branch
        """
        try:
            cmd = "cd {path}; git describe --tags".format(path=self.path)
            return "tag", j.tools.executor.local.execute(cmd)[1]
        except BaseException:
            return "branch", self.repo.head.ref.name

    def getConfig(self, field):
        """
        returns value of provided field name
        returns empty string if not found

        :param fields: field name of the config to search for
        :return: string value of the field name
        """
        cmd = "cd %s; git config %s" % (self.path, field)
        rc, output, _ = j.tools.executor.local.execute(cmd, die=False)
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

        cmd = "cd %s; git config %s %s %s" % (self.path, flags, field, value)
        j.tools.executor.local.execute(cmd, die=die)

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

        cmd = "cd %s; git config --unset %s %s" % (self.path, flags, field)
        j.tools.executor.local.execute(cmd, die=die)
