import os
import git
import uuid
import subprocess

from Jumpscale import j
from loguru import logger
from unittest import skip
from parameterized import parameterized
from pylint.test.functional.invalid_exceptions_caught import EXCEPTION


class Gitclient:
    LOGGER = logger
    LOGGER.add("git_client_{time}.log")
    REPO_LOCATION = "/sandbox/code/github/threefoldtech/jumpscaleX_core/"

    def setUp(self):
        print('\t')
        self.info('Test case : {}'.format(self._testMethodName))

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @staticmethod
    def os_command(command):
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = process.communicate()
        return output, error

    def check_branch(self):
        REPO_LOCATION = "/sandbox/code/github/threefoldtech/jumpscaleX_core/"
        command = "cd {} && cat .git/HEAD".format(REPO_LOCATION)
        output, error = self.os_command(command)
        branch = output.decode()[output.decode().find("head") + 6: -1]
        return branch

    def test001_currentdir_gitrepo(self):
        """TC383
        Test case for currentDirGitRepo method in git client

        **Test scenario**
        #. cd to /sandbox/code/github/threefoldtech/jumpscaleX_core/
        #. create git client and save it.
        #. check that gitclient BASEDIR is /sandbox/code/github/threefoldtech/jumpscaleX_core/
        #. check that gitclient account is threefoldtech
        #. check that gitclient branchName is the same as the current branch
        #. check that gitclient name is jumpscaleX_core

        """
        currentDirectory = os.getcwd()
        self.info("cd to /sandbox/code/github/threefoldtech/jumpscaleX_core/")
        os.chdir('/sandbox/code/github/threefoldtech/jumpscaleX_core/')
        self.info("create git client and save it")
        gitclient = j.clients.git.currentDirGitRepo()
        gitclient.save()
        self.info("check gitclient BASEDIR")
        self.assertEqual('/sandbox/code/github/threefoldtech/jumpscaleX_core', gitclient.BASEDIR)
        self.info("check gitclient account")
        self.assertEqual('threefoldtech', gitclient.account)
        self.info("check gitclient branch")
        branch_name = self.check_branch()
        self.assertEqual(branch_name, gitclient.branchName)
        self.info("check gitclient name")
        self.assertEqual('jumpscaleX_core', gitclient.name)
        os.chdir(currentDirectory)

    def test002_find(self):
        """
        TC386
        Test case for find method in git client
        find the list of repos locations in you system
        the output will be like this:
        ['github', organization, repo_name, repo_path]
        TODO: will make parametrized with the organization name, try to find better way to check the output

        **Test scenario**
        #. check the output of find method in git client
        """
        self.info(
            "find the list of repos locations in you system the output will be like this: ['github', organization, repo_name, repo_path]"
        )
        result_gitclient = j.clients.git.find()
        self.assertIn("jumpscaleX_core", result_gitclient)

    @parameterized.expand(
        [
            ("/test_gitclient/",),
            ("/sandbox/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/clients/git/",)
        ]
    )
    def test003_find_gitpath(self, path):
        """
        TC384
        Test case for findGitPath method in git client
        findGitPath check if this path or any of its parents is a git repo,
                    return the first git repo
        TODO: will be paramterized with True and False.

        **Test scenario**
        #. check the findGitPath method with two input for path option
        #. print an error with /test_gitclient/
        #. print ( /sandbox/code/github/threefoldtech/jumpscaleX_core/ ) for another input

        """
        self.info("check the findGitPath method with two input for path option")
        self.info("print an error with /test_gitclient/ input")
        if path == "/test_gitclient/":
            try:
                j.clients.git.findGitPath(path)
            except EXCEPTION as err:
                self.fail(err)
        else:
            self.info(
                "print /sandbox/code/github/threefoldtech/jumpscaleX_core/ for the other input"
            )
            result = j.clients.git.findGitPath(path)
            self.asserEqual(result, "/sandbox/code/github/threefoldtech/jumpscaleX_core/")

    def test004_get_currentbranch(self):
        """
        TC385
        Test case for getCurrentBranch method in git client

        **Test scenario**
        #. check the branch name in /sandbox/code/github/threefoldtech/jumpscaleX_core/ repo

        """
        self.info("check the branch name in /sandbox/code/github/threefoldtech/jumpscaleX_core/ repo")
        gitclient_currentbranch = j.clients.git.getCurrentBranch("/sandbox/code/github/threefoldtech/jumpscaleX_core/")
        branch_name = self.check_branch()
        self.assertEqual(gitclient_currentbranch, branch_name)

    def test005_getgit_reposlist_local(self):
        """
        TC387
        Test case for getGitReposListLocal method in git client
        find the list of repos locations in you system
        the output will be like this:
        [repo_name, repo_path]
        TODO: add parametrized for provider, account, name, and errorIfNone

        **Test scenario**
        #. check the output of getGitReposListLocal method in git client
        """
        self.info("find the list of repos locations in you system the output will be like this: [repo_name, repo_path]")
        getreposlist = j.clients.git.getGitReposListLocal()
        self.assertIN("/sandbox/code/github/threefoldtech/jumpscaleX_core", getreposlist)

    def test006_pull_git_repo(self):
        """
        TC393
        Test case for pullGitRepo method in git client
        TODO: will add the depth option but trying to find good way to code it

        **Test scenario**
        #. try pullGitRepo with dest option /tmp/test_gitclient/
            && and with url option (https://github.com/threefoldtech/jumpscaleX_threebot.git)
        #. check that the repo in /tmp/test_gitclient/ directory.
        """
        self.info("try pullGitRepo with dest option /tmp/test_gitclient/ and threebot repo as a url")
        j.clients.git.pullGitRepo(
            dest="/tmp/test_gitclient/", url="https://github.com/threefoldtech/jumpscaleX_core.git")
        self.info("check that the repo in /tmp/test_gitclient/ directory")
        output, error = self.os_command("git status")
        self.assertFalse(error)
        self.assertIn("nothing to commit, working tree clean", output.decode())

    def test007_update_git_repos(self):
        """
        TC394
        Test case for updateGitRepos method in git client

        **Test scenario**
        #. clone a repo in /sandbox/code/github/tfttesting/ directory.
        #. create a file with a random name in git directory.
        #. use updateGitRepos to add and commit this file with certain commit message.
        #. check the latest commit on this repo make sure it's the same as the FILE_NAME.
        """
        self.info("clone a repo in /sandbox/code/github/tfttesting/ directory")
        git.Repo.clone_from("https://github.com/tfttesting/updateGitRepos.git", "/sandbox/code/github/tfttesting/")

        self.info("create a file with a random name in git directory")
        FILE_NAME = str(uuid.uuid4()).replace("-", "")[:10]
        with open('/sandbox/code/github/tfttesting/{}.txt'.format(FILE_NAME), 'w') as f:
            data = 'this is new file {}'.format(FILE_NAME)
            f.write(data)

        self.info("use updateGitRepos to add and commit this file with certain commit message")
        j.clients.git.updateGitRepos(provider='github', account='tfttesting', name='updateGitRepos',
                                     message='adding file {}'.format(FILE_NAME))

        self.info("check the latest commit on this repo make sure it's the same as the FILE_NAME")
        repo = git.Repo("/sandbox/code/github/tfttesting/")
        commits = repo.head.log()
        latest_commit = str(commits[-1]).split("commit: ")[-1].replace("\n", "")

        self.assertEqual("adding file {}".format(FILE_NAME), latest_commit)


