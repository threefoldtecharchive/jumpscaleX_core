import os
import unittest
import subprocess
from parameterized import parameterized
from Jumpscale import j
from pylint.test.functional.invalid_exceptions_caught import EXCEPTION


class Gitclient:
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

    def test001_currentDirGitRepo(self):
        """TC
        Test case for currentDirGitRepo method in git client

        **Test scenario**
        #. cd to /sandbox/code/github/threefoldtech/jumpscaleX_core/
        #. create git client and save it.
        #. check that gitclient BASEDIR is /sandbox/code/github/threefoldtech/jumpscaleX_core/
        #. check that gitclient account is threefoldtech
        #. check that gitclient branchName is the same as the current branch
        #. check that gitclient name is jumpscaleX_core

        """
        os.chdir('/sandbox/code/github/threefoldtech/jumpscaleX_core/')
        gitclient = j.clients.git.currentDirGitRepo()
        gitclient.save()
        self.assertEqual('/sandbox/code/github/threefoldtech/jumpscaleX_core', gitclient.BASEDIR)
        self.assertEqual('threefoldtech', gitclient.account)
        branch_name = self.check_branch()
        self.assertEqual(branch_name, gitclient.branchName)
        self.assertEqual('jumpscaleX_core', gitclient.name)
        os.chdir("/root")

    def test002_find(self):
        """
        TC
        Test case for find method in git client
        find the list of repos locations in you system
        the output will be like this:
        ['github', organization, repo_name, repo_path]
        TODO: will make parametrized with the organization name, try to find better way to check the output

        **Test scenario**
        #. check the output of find method in git client
        """
        result_gitclient = j.clients.git.find()
        self.assertIn("jumpscaleX_core", result_gitclient)

    @parameterized.expand(
        [
            ("/test_gitclient/",),
            ("/sandbox/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/clients/git/",)
        ]
    )
    def test003_findGitPath(self, path):
        """
        TC
        Test case for findGitPath method in git client
        findGitPath check if this path or any of its parents is a git repo,
                    return the first git repo
        TODO: will be paramterized with True and False

        **Test scenario**
        #. check the findGitPath method with two input for path option
        #. print an error with /test_gitclient/
        #. print ( /sandbox/code/github/threefoldtech/jumpscaleX_core/ ) for another input

        """
        if path == "/test_gitclient/":
            try:
                j.clients.git.findGitPath(path)
            except EXCEPTION as err:
                self.fail(err)
        else:
            result = j.clients.git.findGitPath(path)
            self.asserEqual(result, "/sandbox/code/github/threefoldtech/jumpscaleX_core/")

    def test004_getCurrentBranch(self):
        """
        TC
        Test case for getCurrentBranch method in git client

        **Test scenario**
        #. check the branch name in /sandbox/code/github/threefoldtech/jumpscaleX_core/ repo

        """
        gitclient_currentbranch = j.clients.git.getCurrentBranch("/sandbox/code/github/threefoldtech/jumpscaleX_core/")
        branch_name = self.check_branch()
        self.assertEqual(gitclient_currentbranch, branch_name)

    def test005_getGitReposListLocal(self):
        """
        TC
        Test case for getGitReposListLocal method in git client
        find the list of repos locations in you system
        the output will be like this:
        [repo_name, repo_path]

        **Test scenario**
        #. check the output of getGitReposListLocal method in git client
        """
        pass

    def test006_pullGitRepo(self):
        """
        TC
        Test case for pullGitRepo method in git client
        TODO: will add the depth option but trying to find good way to code it

        **Test scenario**
        #. try pullGitRepo with dest option /tmp/test_gitclient/
            && and with url option (https://github.com/threefoldtech/jumpscaleX_threebot.git)
        #. check that the repo in /tmp/test_gitclient/ directory.
        """
        j.clients.git.pullGitRepo(
            dest="/tmp/test_gitclient/", url="https://github.com/threefoldtech/jumpscaleX_core.git")
        output, error = self.os_command("git status")
        self.assertFalse(error)
        self.assertIn("nothing to commit, working tree clean", output.decode())
