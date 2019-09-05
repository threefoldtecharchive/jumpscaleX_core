from Jumpscale import j


def main(self):
    """
    kosmos 'j.sal.fs.test("dir_file")'
    """

    j.tools.logger.debug = True

    dir_path_1 = "/test_dir_1/"
    file_1 = "test_file"
    file_1_content = "first"
    file_1_2 = "test_file2"
    file_1_2_content = "third"
    dir_path_2 = "/test_dir_2/"
    file_2 = "test_file"
    file_2_content = "second"
    file_2_2 = "test_second_file_inside_dir_2"
    file_2_2_content = "fourth"
    print("TEST Directory creation")
    if j.sal.fs.exists(dir_path_1):
        j.sal.fs.remove(dir_path_1)
    if j.sal.fs.exists(dir_path_2):
        j.sal.fs.remove(dir_path_2)

    assert j.sal.fs.exists(dir_path_1) == False
    assert j.sal.fs.exists(dir_path_2) == False

    j.sal.fs.createDir(dir_path_1)
    j.sal.fs.createDir(dir_path_2)

    assert j.sal.fs.exists(dir_path_1) == True
    assert j.sal.fs.exists(dir_path_2) == True

    j.sal.fs.writeFile(dir_path_1 + file_1, file_1_content)
    j.sal.fs.writeFile(dir_path_1 + file_1_2, file_1_2_content)
    j.sal.fs.writeFile(dir_path_2 + file_2, file_2_content)
    j.sal.fs.writeFile(dir_path_2 + file_2_2, file_2_2_content)
    assert j.sal.fs.readFile(dir_path_2 + file_2) == file_2_content
    assert j.sal.fs.readFile(dir_path_1 + file_1) == file_1_content
    assert j.sal.fs.readFile(dir_path_1 + file_1_2) == file_1_2_content
    assert j.sal.fs.readFile(dir_path_2 + file_2_2) == file_2_2_content

    assert j.sal.fs.exists(dir_path_1 + file_1) == True
    assert j.sal.fs.exists(dir_path_2 + file_2) == True
    assert j.sal.fs.exists(dir_path_1 + file_1_2) == True
    assert j.sal.fs.isFile(dir_path_1 + file_1) == True
    assert j.sal.fs.isFile(dir_path_2 + file_2) == True
    assert j.sal.fs.isFile(dir_path_1 + file_1_2) == True
    assert j.sal.fs.isFile(dir_path_2 + file_2_2) == True

    print("TEST Directory copy with no overwrites")
    j.sal.fs.copyDirTree(dir_path_1, dir_path_2, overwriteFiles=False)
    assert j.sal.fs.exists(dir_path_1 + file_1) == True
    assert j.sal.fs.exists(dir_path_2 + file_2) == True
    assert j.sal.fs.exists(dir_path_1 + file_1_2) == True
    assert j.sal.fs.isFile(dir_path_1 + file_1) == True
    assert j.sal.fs.isFile(dir_path_2 + file_2) == True
    assert j.sal.fs.isFile(dir_path_1 + file_1_2) == True
    # overwrite is False
    # as file_1 and file_2 names are identical the content should stay the same
    assert j.sal.fs.readFile(dir_path_2 + file_2) == file_2_content
    assert j.sal.fs.readFile(dir_path_1 + file_1) == file_1_content
    # file_1_2 should have been copied to dir2
    assert j.sal.fs.isFile(dir_path_2 + file_1_2) == True
    # extraneous file should have been preserved
    assert j.sal.fs.readFile(dir_path_2 + file_2_2) == file_2_2_content

    print("TEST Directory deletion")
    if j.sal.fs.exists(dir_path_1):
        j.sal.fs.remove(dir_path_1)
    if j.sal.fs.exists(dir_path_2):
        j.sal.fs.remove(dir_path_2)

    print("TEST Directory copy with overwrites")
    j.sal.fs.createDir(dir_path_1)
    j.sal.fs.createDir(dir_path_2)
    j.sal.fs.writeFile(dir_path_1 + file_1, file_1_content)
    j.sal.fs.writeFile(dir_path_1 + file_1_2, file_1_2_content)
    j.sal.fs.writeFile(dir_path_2 + file_2, file_2_content)
    j.sal.fs.writeFile(dir_path_2 + file_2_2, file_2_2_content)
    j.sal.fs.copyDirTree(dir_path_1, dir_path_2, overwriteFiles=True)
    assert j.sal.fs.isFile(dir_path_1 + file_1) == True
    assert j.sal.fs.isFile(dir_path_2 + file_2) == True
    assert j.sal.fs.isFile(dir_path_1 + file_1_2) == True
    # extraneous file should have been deleted
    assert j.sal.fs.exists(dir_path_2 + file_2_2) == False
    # as file_1 and file_2 names are identical the content should have been overwritten
    assert j.sal.fs.readFile(dir_path_2 + file_2) == file_1_content
    assert j.sal.fs.readFile(dir_path_1 + file_1) == file_1_content
    # file_1_2 should have been copied to dir2
    assert j.sal.fs.isFile(dir_path_2 + file_1_2) == True
