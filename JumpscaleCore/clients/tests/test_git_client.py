import os
import unittest
from Jumpscale import j
from testconfig import config
from base_test import BaseTest


class TestGitClient(BaseTest):

    user_name = config["git"]["name"]
    user_email = config["git"]["email"]
    user_passwd = config["git"]["passwd"]
    git_token = config["git"]["token"]
    REPO_DIR = "/tmp/test_tft"
    RANDOM_NAME = j.data.idgenerator.generateXCharID(10)
    REPO_NAME = j.data.idgenerator.generateXCharID(10)
    GIT_REPO = "{}/code/test/tfttesting/{}".format(REPO_DIR, REPO_NAME)

    @classmethod
    def setUpClass(cls):

        cls.info("Create remote repo, in github account")
        cls.github_client = j.clients.github.get(cls.RANDOM_NAME, token=cls.git_token)
        cls.repo = cls.github_client.repo_create(cls.REPO_NAME)

        cls.info("Initialized empty Git repository locally in {}, connect to remote one".format(cls.GIT_REPO))
        j.clients.git.pullGitRepo(dest=cls.GIT_REPO, url=cls.repo.clone_url, ssh=False)

        cls.info("Add README.md file in the git repo")
        with open("/{}/README.md".format(cls.GIT_REPO), "a") as out:
            out.write("README.md" + "\n")
        cls.os_command("cd {} && git add README.md".format(cls.GIT_REPO))

        cls.os_command('git config --global user.email "{}"'.format(cls.user_email))
        cls.os_command('git config --global user.name "{}"'.format(cls.user_name))

        cls.os_command('cd {} && git commit -m "first commit"'.format(cls.GIT_REPO))

        cls.info("Push new changes to the remote git repo")
        cls.os_command(
            "cd {} && git push -u 'https://{}:{}@github.com/{}/{}.git' master".format(
                cls.GIT_REPO, cls.user_name, cls.user_passwd, cls.user_name, cls.REPO_NAME
            )
        )

        cls.info("Create a git client")
        cls.GIT_CLIENT = j.clients.git.get(cls.GIT_REPO)

        cls.info("Grep the Commit_ID")
        output, error = cls.os_command("cd {} && git rev-parse HEAD".format(cls.GIT_REPO))
        cls.C_ID = output.decode().rstrip()

    def setUp(self):
        print("\t")
        self.info("Test case : {}".format(self._testMethodName))

    def tearDown(self):
        self.info("Revoke to {} C_ID".format(self.C_ID))
        self.os_command("cd {} && git reset --hard {} && git checkout master".format(self.GIT_REPO, self.C_ID))

    @classmethod
    def tearDownClass(cls):
        cls.info("Remove remote repo")
        repo = cls.github_client.repo_get(cls.REPO_NAME)
        cls.github_client.repo_delete(repo)

        cls.os_command("rm -rf /tmp/{}".format(cls.REPO_NAME))

        cls.info("Remove git repo directory")
        cls.os_command("rm -rf {}".format(cls.REPO_DIR))

        cls.info("Remove github client")
        cls.github_client.delete()

    def create_two_files(self):
        """
        Method to create 2 files in git repo.
        :return: Name of the files.
        """
        RAND_FILE_1 = self.rand_string()
        RAND_FILE_2 = self.rand_string()

        self.info("Create two files in a git repo directory")
        j.sal.fs.createEmptyFile("{}/{}".format(self.GIT_REPO, RAND_FILE_1))
        j.sal.fs.createEmptyFile("{}/{}".format(self.GIT_REPO, RAND_FILE_2))

        return RAND_FILE_1, RAND_FILE_2

    def get_current_branch_name(self):
        """
        Method to get current branch name.
        :return: Branch_name
        """
        output, error = self.os_command("cd {} && git branch | grep \\* | cut -d ' ' -f2".format(self.GIT_REPO))
        return output.decode().rstrip()

    def get_current_commit_id(self):
        """
        Method to get current Commit_ID
        :return: Commit_ID
        """
        output, error = self.os_command("cd {} && git rev-parse HEAD".format(self.GIT_REPO))
        return output.decode().rstrip()

    def test001_add_files(self):
        """
        TC 480
        Test add new files in git repo.
        **Test scenario**
        #. Create two files in a git repo directory.
        #. Add one of those two file, using addfiles method.
        #. Make sure that this file is added correctly.
        #. Try to add non existing file, should raise an error.
        """
        FILE_1, FILE_2 = self.create_two_files()

        self.info("Add one of those two file, using addfiles method")
        self.GIT_CLIENT.addFiles(files=[FILE_1])

        self.info("Make sure that this file is added correctly")
        output, error = self.os_command("cd {} && git ls-files".format(self.GIT_REPO))
        self.assertIn("{}".format(FILE_1), output.decode())

        self.info("Try to add non existing file, should raise an error")
        with self.assertRaises(Exception) as error:
            self.GIT_CLIENT.addFiles(files=[self.RANDOM_NAME])
            self.assertTrue("No such file or directory" in error.exception.args[0])

    def test002_add_remove_files(self):
        """
        TC 484
        Test add new files and remove deleted ones.
        **Test scenario**
        #. Create two files in a git repo directory FILE_1, FILE_2.
        #. Create another two files FILE_3, FILE_4, add those two files, then remove them.
        #. Use addRemoveFiles method, to add FILE_1, FILE_2 and remove FILE_3, FILE_4.
        #. Make sure that FILE_1, FILE_2 are added, and FILE_3, FILE_4 are removed.
        """
        self.info("Create two files in a git repo directory FILE_1, FILE_2")
        FILE_1, FILE_2 = self.create_two_files()

        self.info("Create another two files FILE_3, FILE_4, add those two files, then remove them")
        FILE_3, FILE_4 = self.create_two_files()
        self.GIT_CLIENT.addFiles(files=[FILE_3, FILE_4])
        self.os_command("cd {} && rm {} {}".format(self.GIT_REPO, FILE_3, FILE_4))

        self.info("Use addRemoveFiles method, to add FILE_1, FILE_2 and remove FILE_3, FILE_4")
        self.GIT_CLIENT.addRemoveFiles()

        self.info("Make sure that FILE_1, FILE_2 are added, and FILE_3, FILE_4 are removed")
        output, error = self.os_command("cd {} && git ls-files".format(self.GIT_REPO))
        self.assertIn(FILE_1 and FILE_2, output.decode())
        self.assertNotIn(FILE_3 and FILE_4, output.decode())

    def test003_check_files_waiting_for_commit(self):
        """
        TC 540
        Test to check if there are files waiting for Commit.
        **Test scenario**
        #. Create two files in a git repo directory.
        #. Check that there are files waiting for commit.
        #. Add those files to git repo.
        #. Recheck if there are files waiting for commit.
        """
        FILE_1, FILE_2 = self.create_two_files()

        self.info("Check that there are files waiting for commit")
        self.assertTrue(self.GIT_CLIENT.checkFilesWaitingForCommit())

        self.info("Add those files to git repo")
        self.GIT_CLIENT.addFiles(files=[FILE_1, FILE_2])

        self.info("Recheck if there are files waiting for commit.")
        self.assertFalse(self.GIT_CLIENT.checkFilesWaitingForCommit())

    def test004_checkout(self):
        """
        TC 541
        test checkout for branch, commit_id, and path.
        For more info, Please visit here https://git-scm.com/docs/git-checkout
        **Test scenario**
        #. Create a new branch and checkout to this branch.
        #. Checkout to master branch.
        #. Check the current Commit_ID (C_ID1).
        #. Create 2 files, add them, then commit.
        #. Use checkout to switch to previous Commit_ID (C_ID1).
        #. Create two new files (FILE_3, FILE_4), then commit, then Remove one of the two files.
        #. Use checkout to return the removed file back.
        #. Check if FILE_1 is back.
        """
        self.info("Create a new branch and checkout to this new created branch")
        BRANCH_NAME = self.rand_string()
        output, error = self.os_command("cd {} && git checkout -b {}".format(self.GIT_REPO, BRANCH_NAME))
        self.assertFalse(error)
        self.assertEqual(BRANCH_NAME, self.get_current_branch_name())

        self.info("Checkout to master branch")
        self.GIT_CLIENT.checkout("master")
        self.assertEqual("master", self.get_current_branch_name())

        self.info("Check the current Commit_ID (C_ID1)")
        C_ID1 = self.get_current_commit_id()

        self.info("Create 2 files, add them, then commit")
        self.create_two_files()
        self.GIT_CLIENT.commit("Add two new files")

        self.info("Use checkout to switch to previous Commit_ID (C_ID1)")
        self.GIT_CLIENT.checkout(C_ID1)

        self.info("Check that checkout is checkout to the previous Commit_ID (C_ID1)")
        self.assertEqual(C_ID1, self.get_current_commit_id())

        self.info("Create two new files (FILE_3, FILE_4), then commit, then Remove one of the two files")
        FILE_3, FILE_4 = self.create_two_files()
        self.GIT_CLIENT.commit("Add two new files")
        os.remove("{}/{}".format(self.GIT_REPO, FILE_3))
        self.assertFalse(os.path.isfile("{}/{}".format(self.GIT_REPO, FILE_3)))

        self.info("Use checkout to return the removed file back")
        self.GIT_CLIENT.checkout("{}/{}".format(self.GIT_REPO, FILE_3))

        self.info("Check if {} is back".format(FILE_3))
        self.assertTrue(os.path.isfile("{}/{}".format(self.GIT_REPO, FILE_3)))

    def test005_commit(self):
        """
        TC 542
        Test commit method which record changes to git repo.
        **Test scenario**
        #. Create two files in a git repo directory.
        #. Edit one of the files, then add it.
        #. Use commit with addremove=False, check the commit_id, Make sure that only one file is added to git repo.
        #. Repeat step 1 again, with addremove=True, and check the output and make sure that the two files are added.
        """
        FILE_1, FILE_2 = self.create_two_files()

        self.info("Edit one of the files, then add it")
        with open("{}/{}".format(self.GIT_REPO, FILE_1), "a") as out:
            out.write("test" + "\n")
        self.GIT_CLIENT.addFiles([FILE_1])

        self.info("Use commit with addremove=False, check the commit_id, Make sure that only one file is added")
        commit = self.GIT_CLIENT.commit(addremove=False)
        commit_1 = commit.hexsha
        self.assertTrue(commit_1)
        output, error = self.os_command("cd {} && git ls-files".format(self.GIT_REPO))
        self.assertNotIn(FILE_2, output.decode())

        self.info("Use commit with addremove=True, and check the output and make sure that the two files are added")
        commit = self.GIT_CLIENT.commit(message="test commit", addremove=True)
        commit_2 = commit.hexsha
        self.assertNotEquals(commit_1, commit_2)
        output, error = self.os_command("cd {} && git ls-files".format(self.GIT_REPO))
        self.assertIn(FILE_2 and FILE_2, output.decode())

    def test006_describe_and_get_branch_or_tag(self):
        """
        TC 543
        Test get Branch or Tag name, and describe option in a git command.
        **Test scenario**
        #. Use describe to check the branch name.
        #. Create new tag.
        #. Use getBranchOrTag, and describe method to get the tag name.
        #. Add new files and commit.
        #. Use getBranchOrTag method to get the branch name.
        #. Use describe method, and check the output something look like this.
            "tag", "1.0-1-gCOMMIT_ID\n"
        """
        self.info("Use describe to check the branch name")
        current_branch = self.get_current_branch_name()
        self.assertEqual("('branch', '{}')".format(current_branch), str(self.GIT_CLIENT.describe()))

        self.info("Create new tag")
        self.os_command("cd {} && git tag 1.0".format(self.GIT_REPO))

        self.info("Use getBranchOrTag, and describe method to get the tag name")
        self.assertEqual(("tag", "1.0"), self.GIT_CLIENT.getBranchOrTag())
        self.assertEqual(("tag", "1.0\n"), self.GIT_CLIENT.describe())

        self.info("Add new files and commit")
        self.create_two_files()
        commit = self.GIT_CLIENT.commit("Add new files and commit")
        Commit_ID = commit.hexsha

        self.info("Use getBranchOrTag method to get the branch name")
        self.assertEqual(
            "('branch', '{}')".format(self.get_current_branch_name()), str(self.GIT_CLIENT.getBranchOrTag())
        )

        self.info("Use describe method and check the output")
        self.assertEqual(("tag", "1.0-1-g{}\n".format(Commit_ID[0:7])), self.GIT_CLIENT.describe())

    def test007_get_changed_files(self):
        """
        TC
        Test getChangedFiles which lists all changed files since certain ref (Commit_ID).
        **Test scenario**
        #. Grep the current Commit_ID C_ID1.
        #. Add 2 files (FILE_1, FILE_2) to git repo, then commit.
        #. Grep the new Commit_ID C_ID2.
        #. Use getChangedFiles method to get those two files from C_ID1 to C_ID2.
        """

        self.info("Grep the current C_ID1")
        C_ID1 = self.get_current_commit_id()

        self.info("Add 2 files to git repo, then commit")
        FILE_1, FILE_2 = self.create_two_files()
        C_ID2 = self.GIT_CLIENT.commit("Add 2 files to git repo")

        self.info("Use getChangedFiles method to get those two files from C_ID1 to C_ID2")
        self.assertEqual(
            sorted([FILE_1, FILE_2]), sorted(self.GIT_CLIENT.getChangedFiles(fromref=C_ID1, toref=C_ID2.hexsha))
        )

    def test008_git_config(self):
        """
        TC 545
        Test get config value to certain git config field.
        **Test scenario**
        #. Use getconfig to get the value of certain git config field.
        #. Redo step 1 again, but with non valid value.
        """
        self.info("Use getconfig to get the value of certain git config field")
        self.GIT_CLIENT.setConfig("user.name", self.user_name, local=False)
        self.assertEqual(self.user_name, self.GIT_CLIENT.getConfig("user.name"))

        self.info("Redo step 1 again, but with non valid value")
        self.assertFalse(self.GIT_CLIENT.getConfig(self.RANDOM_NAME))

    def test009_get_modified_files(self):
        """
        TC 547
        Test to get the modified files.
        NOTE:
            - we can use collapse=(True or False) by default it's False, if we use collapse=True
            the output will be printed in a list, but if we use collapse=False the output will be the list of modified
            files separated in dict of 4 lists
            {'D': [], 'N': [], 'M': [], 'R': []}, where D:deleted, N:new, M:modified, R:renamed.
            - Also, we have ignore, for files to ignore.
        **Test scenario**
        #. Create two files (FILE_1, FILE_2) in a git repo directory.
        #. Use getModifiedFiles to test that those two files are added.
        #. Delete one of those two files, and check if it is deleted.
        #. Use getModifiedFiles with options (collapse, ignore), and check the output.
        """
        FILE_1, FILE_2 = self.create_two_files()
        self.info("Use getModifiedFiles to test that those two files are added")
        NEW_FILES = [val for key, val in self.GIT_CLIENT.getModifiedFiles().items() if "N" in key]
        self.assertEqual(sorted(NEW_FILES[0]), sorted([FILE_1, FILE_2]))

        self.info("Delete one of those two files, and check if it is deleted")
        self.GIT_CLIENT.addFiles([FILE_1, FILE_2])
        os.remove("{}/{}".format(self.GIT_REPO, FILE_1))
        DELETED_FILE = [val for key, val in self.GIT_CLIENT.getModifiedFiles().items() if "D" in key]
        self.assertEqual([[FILE_1]], DELETED_FILE)

        self.info("Use getModifiedFiles with (collapse, ignore) options")
        FILE_3, FILE_4 = self.create_two_files()
        self.assertIn(FILE_4, self.GIT_CLIENT.getModifiedFiles(collapse=True, ignore=[FILE_3]))
        self.assertNotIn(FILE_3, self.GIT_CLIENT.getModifiedFiles(collapse=True, ignore=[FILE_3]))

    def test010_has_modified_files(self):
        """
        TC 548
        Test hasModifiedFiles which returns True if there is any file modified, new, renamed, or deleted and
        has not been yet committed, False otherwise.
        **Test scenario**
        #. Create two files in a git repo directory.
        #. Use hasModifiedFiles to check the output, should be True.
        #. Add those files and recheck, the output should be false.
        """
        FILE_1, FILE_2 = self.create_two_files()

        self.info("Use hasModifiedFiles to check the output")
        self.assertTrue(self.GIT_CLIENT.hasModifiedFiles())

        self.info("Add those files {}, {}".format(FILE_1, FILE_2))
        self.GIT_CLIENT.commit()

        self.info("Check again after we add the files")
        self.assertFalse(self.GIT_CLIENT.hasModifiedFiles())

    def test011_patch_git_ignore(self):
        """
        TC 551
        Test patch gitignore file in git repo.
        **Test scenario**
        #. Make sure that .gitignore file doesn't exist.
        #. Use patchGitignore method and check if .gitignore file is created.
        #. Remove .gitignore file
        """
        self.info("Make sure that .gitignore file doesn't exist")
        self.assertFalse(os.path.isfile("{}/.gitignore".format(self.GIT_REPO)))

        self.info("Use patchGitignore and check if .gitignore file is created")
        self.GIT_CLIENT.patchGitignore()
        self.assertTrue(os.path.isfile("{}/.gitignore".format(self.GIT_REPO)))

        self.info("Remove .gitignore file")
        os.remove("{}/.gitignore".format(self.GIT_REPO))

    def test012_pull(self):
        """
        TC 552
        Test pull from the remote repo.
        **Test scenario**
        #. Clone the remote directory in /tmp/.
        #. Create a file in the new cloned repo and commit, then push.
        #. Pull the latest changes in the old git client repo.
        #. Check the existing of the files in the old repo.
        #. Create 2 files.
        #. Commit the two files.
        #. Use pull method with files waiting to commit, should raise an Exception.
        """

        self.info("Clone the remote directory in /tmp/")
        self.os_command("cd /tmp/ && git clone https://github.com/{}/{}.git".format(self.user_name, self.REPO_NAME))

        self.info("Create a file in the new directory and commit, then push")
        FILE = self.RANDOM_NAME
        self.os_command("cd /tmp/{} && touch {}".format(self.REPO_NAME, FILE))

        self.os_command('cd /tmp/{} && git add {} && git commit -m "third file"'.format(self.REPO_NAME, FILE))
        self.os_command(
            "cd /tmp/{} && git push -u 'https://{}:{}@github.com/{}/{}.git' master".format(
                self.REPO_NAME, self.user_name, self.user_passwd, self.user_name, self.REPO_NAME
            )
        )

        self.info("Pull the latest changes")
        self.GIT_CLIENT.pull()

        self.info("Check that the new created created file is existing after pull")
        self.assertTrue(os.path.isfile("{}/{}".format(self.GIT_REPO, FILE)))

        self.info("Create 2 files")
        self.create_two_files()

        self.info("Commit the two files")
        self.GIT_CLIENT.commit("Add the two files")

        self.info("Use pull method with files waiting to commit, should raise an Exception")
        with self.assertRaises(Exception) as error:
            self.GIT_CLIENT.pull()
            self.assertTrue("files waiting to commit" in error.exception.args[0])

    @unittest.skip("should run manually")
    def test013_push(self):
        """
        TC 553
        **Test scenario**
        #. Create 2 files (File_1, File_2).
        #. Commit changes in the local repo, using commit method in git client.
        #. Push changes to the remote repo, using push method.
        """
        self.info("Create 2 files (File_1, File_2)")
        self.create_two_files()

        self.info("Commit the two files")
        self.GIT_CLIENT.commit("Add the two files")

        self.info("Push changes to the remote repo, using push method")
        self.GIT_CLIENT.push()

    def test014_remove_files(self):
        """
        TC 555
        Test remove files from git repo.
        **Test scenario**
        #. Create two files in a git repo directory.
        #. Use removeFiles, and check if those files are deleted.
        #. Try to use removeFiles to check non existing file, should raise an error.
        """
        FILE_1, FILE_2 = self.create_two_files()
        self.GIT_CLIENT.addFiles([FILE_1, FILE_2])

        self.info("Use removeFiles, and check if those files are deleted")
        self.GIT_CLIENT.removeFiles([FILE_2])
        output, error = self.os_command("cd {} && git ls-files".format(self.GIT_REPO))
        self.assertNotIn("{}".format(FILE_2), output.decode())

        self.info("Try to use removeFiles to check non existing file")
        with self.assertRaises(Exception) as error:
            self.GIT_CLIENT.removeFiles(files=[self.RANDOM_NAME])
            self.assertTrue("did not match any files" in error.exception.args[0])

    def test015_setConfig_and_unset_config(self):
        """
        TC 556
        Test set and unset new config values to certain config fields.
        **Test scenario**
        #. Set user mail.
        #. Try to set non valid field.
        #. Unset the email.
        """
        self.info("Set user mail")
        self.GIT_CLIENT.setConfig("user.email", self.user_email, local=False)
        self.assertEqual(self.user_email, self.GIT_CLIENT.getConfig("user.email"))

        self.info("Try to set non valid field")
        with self.assertRaises(Exception) as error:
            self.GIT_CLIENT.setConfig("NON_VALID", "NON_VALID", local=False)
            self.assertTrue("key does not contain a section" in error.exception.args[0])

        self.info("Unset the email")
        self.GIT_CLIENT.unsetConfig("user.email", local=False)

    def test016_set_remote_urL(self):
        """
        TC 557
        Test set remote url which change remote URL from HTTPS to SSH.
        **Test scenario**
        #. Change remote URL to SSH.
        #. Use gitconfig method to check that URL is changed.
        #. Reset remote URL to HTTPS again.
        """
        self.info("Change remote URL to SSH")
        self.GIT_CLIENT.setRemoteURL("git@github.com:{}/{}.git".format(self.user_name, self.REPO_NAME))

        self.info("Use gitconfig method to check that URL is changed")
        self.assertEqual(
            "git@github.com:{}/{}.git".format(self.user_name, self.REPO_NAME),
            self.GIT_CLIENT.getConfig("remote.origin.url"),
        )

        self.info("Reset remote URL to HTTPS again")
        self.GIT_CLIENT.setRemoteURL("https://github.com/tfttesting/new_test_test.git")

    def test017_switch_branch(self):
        """
        TC 558
        Test switch branch in git repo.
        **Test scenario**
        #. Create new branch.
        #. Use switchBranch with (non existing branch name, create=True).
        #. Use switchBranch with (existing branch name, create=False).
        #. Use switchBranch with (non existing branch name, create=False).
        """
        self.info("Create new branch")
        branch_1 = self.rand_string()
        self.os_command("cd {} && git checkout -b {}".format(self.GIT_REPO, branch_1))

        self.info("Use switchBranch with (non existing branch name, create=True)")
        branch_2 = self.rand_string()
        self.GIT_CLIENT.switchBranch(branch_2, create=True)
        self.assertEqual(branch_2, self.get_current_branch_name())

        self.info("Use switchBranch with (existing branch name, create=False)")
        self.GIT_CLIENT.switchBranch(branch_2, create=False)
        self.assertEqual(branch_2, self.get_current_branch_name())

        self.info("Use switchBranch with (non existing branch name, create=False)")
        with self.assertRaises(Exception) as error:
            self.GIT_CLIENT.switchBranch(self.RANDOM_NAME, create=False)
            self.assertTrue("did not match any file(s) known to git" in error.exception.args[0])
