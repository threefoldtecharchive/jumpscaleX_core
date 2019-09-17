from Jumpscale import j


def main(self):
    """
    kosmos 'j.sal.fs.test("hash")'
    """

    j.tools.logger.debug = True

    test_path = "/tmp/test_dir/"
    moved_path = "~/tmp2/another_test_dir/"
    file_path = "test.txt"
    file2_path = "test2.txt"
    file_content = "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor"

    print("TEST getFolderMD5sum")
    if j.sal.fs.exists(test_path):
        j.sal.fs.remove(test_path)
    if j.sal.fs.exists(moved_path):
        j.sal.fs.remove(moved_path)

    j.sal.fs.createDir(test_path)

    assert j.sal.fs.exists(test_path) == True

    j.sal.fs.writeFile(test_path + file_path, file_content)
    assert j.sal.fs.isFile(test_path + file_path) == True
    hash_dir = j.sal.fs.getFolderMD5sum(test_path)
    print("Dir hash:%s" % hash_dir)
    hash_file = j.sal.fs.md5sum(test_path + file_path)
    print("file hash:%s" % hash_file)
    assert hash_dir != hash_file
    assert hash_file == "af270cdfadd7512a60c7558dd0458db0"
    assert hash_dir == "8610d1c0268528b50e0a1099df3d9d74"

    # let's move the directory to another place the hash should be the same
    j.sal.fs.moveDir(test_path, moved_path)
    assert j.sal.fs.exists(moved_path) == True
    assert j.sal.fs.isFile(moved_path + file_path) == True
    hash_moved_file = j.sal.fs.md5sum(moved_path + file_path)
    hash_moved_dir = j.sal.fs.getFolderMD5sum(moved_path)
    assert hash_dir == hash_moved_dir
    assert hash_file == hash_moved_file
    j.sal.fs.moveDir(moved_path, test_path)

    # let's add another file with same content
    j.sal.fs.writeFile(test_path + file2_path, file_content)
    files = j.sal.fs.listFilesInDir(test_path)
    assert len(files) == 2
    hash_dir_2 = j.sal.fs.getFolderMD5sum(test_path)
    assert hash_dir != hash_dir_2
    hash_file_2 = j.sal.fs.md5sum(test_path + file2_path)
    assert hash_file == hash_file_2

    # we remove the file to replace it with a file with same name but different content
    j.sal.fs.remove(test_path + file2_path)
    assert j.sal.fs.exists(test_path + file2_path) == False
    j.sal.fs.writeFile(test_path + file2_path, file_content + hash_file)
    hash_dir_3 = j.sal.fs.getFolderMD5sum(test_path)
    assert hash_dir != hash_dir_2 != hash_dir_3
    hash_file_3 = j.sal.fs.md5sum(test_path + file2_path)
    assert hash_file != hash_file_3

    j.sal.fs.remove(test_path)
