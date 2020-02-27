import logging
import os
from Jumpscale import j

j.builders.runtimes.python3.pip_package_install("nose-testconfig")

from subprocess import Popen, PIPE

skip = j.baseclasses.testtools._skip


try:
    user_name = os.environ["GIT_NAME"]
    user_email = os.environ["GIT_EMAIL"]
    user_passwd = os.environ["GIT_PASSWORD"]
    git_token = os.environ["GIT_TOKEN"]
except KeyError:
    raise Exception("You need to set git username, email, password, and token as an environmental variables")

REPO_DIR = "/tmp/test_tft"
RANDOM_NAME = j.data.idgenerator.generateXCharID(10)
REPO_NAME = j.data.idgenerator.generateXCharID(10)
GIT_REPO = "{}/code/test/tfttesting/{}".format(REPO_DIR, REPO_NAME)
GIT_CLIENT = ""
github_client = ""
C_ID = ""


def info(message):
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    logging.info(message)


def rand_string():
    return j.data.idgenerator.generateXCharID(10)


@skip("https://github.com/threefoldtech/zeroCI/issues/30, This test can be run manually")
def before_all():

    info("Create remote repo, in github account")
    global github_client
    github_client = j.clients.github.get(RANDOM_NAME, token=git_token)
    repo = github_client.repo_create(REPO_NAME)

    info("Initialized empty Git repository locally in {}, connect to remote one".format(GIT_REPO))
    j.clients.git.pullGitRepo(dest=GIT_REPO, url=repo.clone_url, ssh=False)

    info("Add README.md file in the git repo")
    with open("/{}/README.md".format(GIT_REPO), "a") as out:
        out.write("README.md" + "\n")
    j.sal.process.execute("cd {} && git add README.md".format(GIT_REPO))

    j.sal.process.execute('git config --global user.email "{}"'.format(user_email))
    j.sal.process.execute('git config --global user.name "{}"'.format(user_name))

    j.sal.process.execute('cd {} && git commit -m "first commit"'.format(GIT_REPO))

    info("Push new changes to the remote git repo")
    j.sal.process.execute(
        "cd {} && git push -u 'https://{}:{}@github.com/{}/{}.git' master".format(
            GIT_REPO, user_name, user_passwd, user_name, REPO_NAME
        )
    )

    info("Create a git client")
    global GIT_CLIENT
    GIT_CLIENT = j.clients.git.get(GIT_REPO)

    info("Grep the Commit_ID")
    _, output, error = j.sal.process.execute("cd {} && git rev-parse HEAD".format(GIT_REPO))
    global C_ID
    C_ID = output.rstrip()


def after():
    info("Revoke to {} C_ID".format(C_ID))
    _, output, error = j.sal.process.execute(
        "cd {} && git reset --hard {} && git checkout master".format(GIT_REPO, C_ID)
    )


def after_all():
    info("Remove remote repo")
    repo = github_client.repo_get(REPO_NAME)
    github_client.repo_delete(repo)

    j.sal.process.execute("rm -rf /tmp/{}".format(REPO_NAME))

    info("Remove git repo directory")
    j.sal.process.execute("rm -rf {}".format(REPO_DIR))

    info("Remove github client")
    github_client.delete()


def create_two_files():
    """
    Method to create 2 files in git repo.
    :return: Name of the files.
    """
    RAND_FILE_1 = rand_string()
    RAND_FILE_2 = rand_string()

    info("Create two files in a git repo directory")
    j.sal.fs.createEmptyFile("{}/{}".format(GIT_REPO, RAND_FILE_1))
    j.sal.fs.createEmptyFile("{}/{}".format(GIT_REPO, RAND_FILE_2))

    return RAND_FILE_1, RAND_FILE_2


def get_current_branch_name():
    """
    Method to get current branch name.
    :return: Branch_name
    """
    _, output, error = j.sal.process.execute("cd {} && git branch | grep \\* | cut -d ' ' -f2".format(GIT_REPO))
    return output.rstrip()


def get_current_commit_id():
    """
    Method to get current Commit_ID
    :return: Commit_ID
    """
    _, output, error = j.sal.process.execute("cd {} && git rev-parse HEAD".format(GIT_REPO))
    return output.rstrip()


def test001_add_files():
    """
    TC 480
    Test add new files in git repo.
    **Test scenario**
    #. Create two files in a git repo directory.
    #. Add one of those two file, using addfiles method.
    #. Make sure that this file is added correctly.
    #. Try to add non existing file, should raise an error.
    """
    FILE_1, FILE_2 = create_two_files()

    info("Add one of those two file, using addfiles method")
    GIT_CLIENT.addFiles(files=[FILE_1])

    info("Make sure that this file is added correctly")
    _, output, error = j.sal.process.execute("cd {} && git ls-files".format(GIT_REPO))
    assert "{}".format(FILE_1) in output

    info("Try to add non existing file, should raise an error")
    # with assertRaises(Exception) as error:
    #     GIT_CLIENT.addFiles(files=[RANDOM_NAME])
    #     assertTrue("No such file or directory" in error.exception.args[0])


def test002_add_remove_files():
    """
    TC 484
    Test add new files and remove deleted ones.
    **Test scenario**
    #. Create two files in a git repo directory FILE_1, FILE_2.
    #. Create another two files FILE_3, FILE_4, add those two files, then remove them.
    #. Use addRemoveFiles method, to add FILE_1, FILE_2 and remove FILE_3, FILE_4.
    #. Make sure that FILE_1, FILE_2 are added, and FILE_3, FILE_4 are removed.
    """
    info("Create two files in a git repo directory FILE_1, FILE_2")
    FILE_1, FILE_2 = create_two_files()

    info("Create another two files FILE_3, FILE_4, add those two files, then remove them")
    FILE_3, FILE_4 = create_two_files()
    GIT_CLIENT.addFiles(files=[FILE_3, FILE_4])
    j.sal.process.execute("cd {} && rm {} {}".format(GIT_REPO, FILE_3, FILE_4))

    info("Use addRemoveFiles method, to add FILE_1, FILE_2 and remove FILE_3, FILE_4")
    GIT_CLIENT.addRemoveFiles()

    info("Make sure that FILE_1, FILE_2 are added, and FILE_3, FILE_4 are removed")
    _, output, error = j.sal.process.execute("cd {} && git ls-files".format(GIT_REPO))
    assert FILE_1 and FILE_2 in output
    assert FILE_3 and FILE_4 not in output


def test003_check_files_waiting_for_commit():
    """
    TC 540
    Test to check if there are files waiting for Commit.
    **Test scenario**
    #. Create two files in a git repo directory.
    #. Check that there are files waiting for commit.
    #. Add those files to git repo.
    #. Recheck if there are files waiting for commit.
    """
    FILE_1, FILE_2 = create_two_files()

    info("Check that there are files waiting for commit")
    assert GIT_CLIENT.checkFilesWaitingForCommit()

    info("Add those files to git repo")
    GIT_CLIENT.addFiles(files=[FILE_1, FILE_2])

    info("Recheck if there are files waiting for commit.")
    assert GIT_CLIENT.checkFilesWaitingForCommit() is False


def test004_checkout():
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
    info("Create a new branch and checkout to this new created branch")
    BRANCH_NAME = rand_string()
    j.sal.process.execute("cd {} && git checkout -b {}".format(GIT_REPO, BRANCH_NAME))
    assert BRANCH_NAME == get_current_branch_name()

    info("Checkout to master branch")
    GIT_CLIENT.checkout("master")
    assert "master" == get_current_branch_name()

    info("Check the current Commit_ID (C_ID1)")
    C_ID1 = get_current_commit_id()

    info("Create 2 files, add them, then commit")
    create_two_files()
    GIT_CLIENT.commit("Add two new files")

    info("Use checkout to switch to previous Commit_ID (C_ID1)")
    GIT_CLIENT.checkout(C_ID1)

    info("Check that checkout is checkout to the previous Commit_ID (C_ID1)")
    assert C_ID1 == get_current_commit_id()

    info("Create two new files (FILE_3, FILE_4), then commit, then Remove one of the two files")
    FILE_3, FILE_4 = create_two_files()
    GIT_CLIENT.commit("Add two new files")
    os.remove("{}/{}".format(GIT_REPO, FILE_3))
    assert os.path.isfile("{}/{}".format(GIT_REPO, FILE_3)) is False

    info("Use checkout to return the removed file back")
    GIT_CLIENT.checkout("{}/{}".format(GIT_REPO, FILE_3))

    info("Check if {} is back".format(FILE_3))
    assert os.path.isfile("{}/{}".format(GIT_REPO, FILE_3))


def test005_commit():
    """
    TC 542
    Test commit method which record changes to git repo.
    **Test scenario**
    #. Create two files in a git repo directory.
    #. Edit one of the files, then add it.
    #. Use commit with addremove=False, check the commit_id, Make sure that only one file is added to git repo.
    #. Repeat step 1 again, with addremove=True, and check the output and make sure that the two files are added.
    """
    FILE_1, FILE_2 = create_two_files()

    info("Edit one of the files, then add it")
    with open("{}/{}".format(GIT_REPO, FILE_1), "a") as out:
        out.write("test" + "\n")
    GIT_CLIENT.addFiles([FILE_1])

    info("Use commit with addremove=False, check the commit_id, Make sure that only one file is added")
    commit = GIT_CLIENT.commit(addremove=False)
    commit_1 = commit.hexsha
    assert commit_1
    _, output, error = j.sal.process.execute("cd {} && git ls-files".format(GIT_REPO))
    assert FILE_2 not in output

    info("Use commit with addremove=True, and check the output and make sure that the two files are added")
    commit = GIT_CLIENT.commit(message="test commit", addremove=True)
    commit_2 = commit.hexsha
    assert commit_1 != commit_2
    _, output, error = j.sal.process.execute("cd {} && git ls-files".format(GIT_REPO))
    assert FILE_2 and FILE_2 in output


def test006_describe_and_get_branch_or_tag():
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
    info("Use describe to check the branch name")
    current_branch = get_current_branch_name()
    assert "('branch', '{}')".format(current_branch) == str(GIT_CLIENT.describe())

    info("Create new tag")
    j.sal.process.execute("cd {} && git tag 1.0".format(GIT_REPO))

    info("Use getBranchOrTag, and describe method to get the tag name")
    assert ("tag", "1.0") == GIT_CLIENT.getBranchOrTag()
    assert ("tag", "1.0\n") == GIT_CLIENT.describe()

    info("Add new files and commit")
    create_two_files()
    commit = GIT_CLIENT.commit("Add new files and commit")
    Commit_ID = commit.hexsha

    info("Use getBranchOrTag method to get the branch name")
    assert "('branch', '{}')".format(get_current_branch_name()) == str(GIT_CLIENT.getBranchOrTag())

    info("Use describe method and check the output")
    assert ("tag", "1.0-1-g{}\n".format(Commit_ID[0:7])) == GIT_CLIENT.describe()


def test007_get_changed_files():
    """
    TC
    Test getChangedFiles which lists all changed files since certain ref (Commit_ID).
    **Test scenario**
    #. Grep the current Commit_ID C_ID1.
    #. Add 2 files (FILE_1, FILE_2) to git repo, then commit.
    #. Grep the new Commit_ID C_ID2.
    #. Use getChangedFiles method to get those two files from C_ID1 to C_ID2.
    """

    info("Grep the current C_ID1")
    C_ID1 = get_current_commit_id()

    info("Add 2 files to git repo, then commit")
    FILE_1, FILE_2 = create_two_files()
    C_ID2 = GIT_CLIENT.commit("Add 2 files to git repo")

    info("Use getChangedFiles method to get those two files from C_ID1 to C_ID2")
    assert sorted([FILE_1, FILE_2]) == sorted(GIT_CLIENT.getChangedFiles(fromref=C_ID1, toref=C_ID2.hexsha))


def test008_git_config():
    """
    TC 545
    Test get config value to certain git config field.
    **Test scenario**
    #. Use getconfig to get the value of certain git config field.
    """
    info("Use getconfig to get the value of certain git config field")
    GIT_CLIENT.setConfig("user.name", user_name, local=False)
    assert user_name == GIT_CLIENT.getConfig("user.name")


def test009_get_modified_files():
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
    FILE_1, FILE_2 = create_two_files()
    info("Use getModifiedFiles to test that those two files are added")
    NEW_FILES = [val for key, val in GIT_CLIENT.getModifiedFiles().items() if "N" in key]
    assert sorted(NEW_FILES[0]) == sorted([FILE_1, FILE_2])

    info("Delete one of those two files, and check if it is deleted")
    GIT_CLIENT.addFiles([FILE_1, FILE_2])
    os.remove("{}/{}".format(GIT_REPO, FILE_1))
    DELETED_FILE = [val for key, val in GIT_CLIENT.getModifiedFiles().items() if "D" in key]
    assert [[FILE_1]] == DELETED_FILE

    info("Use getModifiedFiles with (collapse, ignore) options")
    FILE_3, FILE_4 = create_two_files()
    assert FILE_4 in GIT_CLIENT.getModifiedFiles(collapse=True, ignore=[FILE_3])
    assert FILE_3 not in GIT_CLIENT.getModifiedFiles(collapse=True, ignore=[FILE_3])


def test010_has_modified_files():
    """
    TC 548
    Test hasModifiedFiles which returns True if there is any file modified, new, renamed, or deleted and
    has not been yet committed, False otherwise.
    **Test scenario**
    #. Create two files in a git repo directory.
    #. Use hasModifiedFiles to check the output, should be True.
    #. Add those files and recheck, the output should be false.
    """
    FILE_1, FILE_2 = create_two_files()

    info("Use hasModifiedFiles to check the output")
    assert GIT_CLIENT.hasModifiedFiles()

    info("Add those files {}, {}".format(FILE_1, FILE_2))
    GIT_CLIENT.commit()

    info("Check again after we add the files")
    assert GIT_CLIENT.hasModifiedFiles() is False


def test011_patch_git_ignore():
    """
    TC 551
    Test patch gitignore file in git repo.
    **Test scenario**
    #. Make sure that .gitignore file doesn't exist.
    #. Use gitignore_patch method and check if .gitignore file is created.
    #. Remove .gitignore file
    """
    info("Make sure that .gitignore file doesn't exist")
    assert os.path.isfile("{}/.gitignore".format(GIT_REPO)) is False

    info("Use gitignore_patch and check if .gitignore file is created")
    GIT_CLIENT.gitignore_patch()
    assert os.path.isfile("{}/.gitignore".format(GIT_REPO))

    info("Remove .gitignore file")
    os.remove("{}/.gitignore".format(GIT_REPO))


def test012_pull():
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

    info("Clone the remote directory in /tmp/")
    j.sal.process.execute("cd /tmp/ && git clone https://github.com/{}/{}.git".format(user_name, REPO_NAME))

    info("Create a file in the new directory and commit, then push")
    FILE = RANDOM_NAME
    j.sal.process.execute("cd /tmp/{} && touch {}".format(REPO_NAME, FILE))

    j.sal.process.execute('cd /tmp/{} && git add {} && git commit -m "third file"'.format(REPO_NAME, FILE))
    j.sal.process.execute(
        "cd /tmp/{} && git push -u 'https://{}:{}@github.com/{}/{}.git' master".format(
            REPO_NAME, user_name, user_passwd, user_name, REPO_NAME
        )
    )

    info("Pull the latest changes")
    GIT_CLIENT.pull()

    info("Check that the new created created file is existing after pull")
    assert os.path.isfile("{}/{}".format(GIT_REPO, FILE))

    info("Create 2 files")
    create_two_files()

    info("Commit the two files")
    GIT_CLIENT.commit("Add the two files")

    info("Use pull method with files waiting to commit, should raise an Exception")
    # with assertRaises(Exception) as error:
    #     GIT_CLIENT.pull()
    #     assertTrue("files waiting to commit" in error.exception.args[0])


@skip("should run manually")
def test013_push():
    """
    TC 553
    **Test scenario**
    #. Create 2 files (File_1, File_2).
    #. Commit changes in the local repo, using commit method in git client.
    #. Push changes to the remote repo, using push method.
    """
    info("Create 2 files (File_1, File_2)")
    create_two_files()

    info("Commit the two files")
    GIT_CLIENT.commit("Add the two files")

    info("Push changes to the remote repo, using push method")
    GIT_CLIENT.push()


def test014_remove_files():
    """
    TC 555
    Test remove files from git repo.
    **Test scenario**
    #. Create two files in a git repo directory.
    #. Use removeFiles, and check if those files are deleted.
    #. Try to use removeFiles to check non existing file, should raise an error.
    """
    FILE_1, FILE_2 = create_two_files()
    GIT_CLIENT.addFiles([FILE_1, FILE_2])

    info("Use removeFiles, and check if those files are deleted")
    GIT_CLIENT.removeFiles([FILE_2])
    _, output, error = j.sal.process.execute("cd {} && git ls-files".format(GIT_REPO))
    assert "{}".format(FILE_2) not in output

    info("Try to use removeFiles to check non existing file")
    # with assertRaises(Exception) as error:
    #     GIT_CLIENT.removeFiles(files=[RANDOM_NAME])
    #     assertTrue("did not match any files" in error.exception.args[0])


def test015_setConfig_and_unset_config():
    """
    TC 556
    Test set and unset new config values to certain config fields.
    **Test scenario**
    #. Set user mail.
    #. Try to set non valid field.
    #. Unset the email.
    """
    info("Set user mail")
    GIT_CLIENT.setConfig("user.email", user_email, local=False)
    assert user_email == GIT_CLIENT.getConfig("user.email")

    info("Try to set non valid field")
    # with assertRaises(Exception) as error:
    #     GIT_CLIENT.setConfig("NON_VALID", "NON_VALID", local=False)
    #     assertTrue("key does not contain a section" in error.exception.args[0])

    info("Unset the email")
    GIT_CLIENT.unsetConfig("user.email", local=False)


def test016_set_remote_urL():
    """
    TC 557
    Test set remote url which change remote URL from HTTPS to SSH.
    **Test scenario**
    #. Change remote URL to SSH.
    #. Use gitconfig method to check that URL is changed.
    #. Reset remote URL to HTTPS again.
    """
    info("Change remote URL to SSH")
    GIT_CLIENT.setRemoteURL("git@github.com:{}/{}.git".format(user_name, REPO_NAME))

    info("Use gitconfig method to check that URL is changed")
    assert "git@github.com:{}/{}.git".format(user_name, REPO_NAME) == GIT_CLIENT.getConfig("remote.origin.url")

    info("Reset remote URL to HTTPS again")
    GIT_CLIENT.setRemoteURL("https://github.com/tfttesting/new_test_test.git")


def test017_switch_branch():
    """
    TC 558
    Test switch branch in git repo.
    **Test scenario**
    #. Create new branch.
    #. Use switchBranch with (non existing branch name, create=True).
    #. Use switchBranch with (existing branch name, create=False).
    #. Use switchBranch with (non existing branch name, create=False).
    """
    info("Create new branch")
    branch_1 = rand_string()
    j.sal.process.execute("cd {} && git checkout -b {}".format(GIT_REPO, branch_1))

    info("Use switchBranch with (non existing branch name, create=True)")
    branch_2 = rand_string()
    GIT_CLIENT.switchBranch(branch_2, create=True)
    assert branch_2 == get_current_branch_name()

    info("Use switchBranch with (existing branch name, create=False)")
    GIT_CLIENT.switchBranch(branch_2, create=False)
    assert branch_2 == get_current_branch_name()

    info("Use switchBranch with (non existing branch name, create=False)")
    # with assertRaises(Exception) as error:
    #     GIT_CLIENT.switchBranch(RANDOM_NAME, create=False)
    #     assertTrue("did not match any file(s) known to git" in error.exception.args[0])
