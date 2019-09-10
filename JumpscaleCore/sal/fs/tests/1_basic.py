from Jumpscale import j
from unittest import TestCase


def main(self):
    """
    kosmos 'j.sal.fs.test("basic")'
    """

    j.tools.logger.debug = True
    test_case = TestCase()
    sandbox_path = "/sandbox"
    inexistant_dir_path = "/64ds6d4s67f6d7f6sd4f6s4/Fsdfsdgjhgsdjfgsj/"
    inexistant_file_path = inexistant_dir_path + "42_yolo.bmat"
    prio_path = "/root/tmp/33_adoc.doc/"
    sandbox_path2 = "/sandbox/"
    long_file_path = "/opt/qbase3/apps/specs/myspecs/definitions/cloud/datacenter.txt"

    print("TEST getDirName")
    # getDirName("/opt/qbase/bin/something/test.py", levelsUp=0) would return something
    path = j.sal.fs.getDirName(long_file_path, levelsUp=0)
    assert not path is None and path != ""
    # e.g. ...getDirName("/opt/qbase/bin/something/test.py", levelsUp=1) would return bin
    path = j.sal.fs.getDirName(long_file_path, levelsUp=1)
    assert path == "definitions"
    # e.g. ...getDirName("/opt/qbase/bin/something/test.py", levelsUp=10) would raise an error
    with test_case.assertRaises(Exception) as cm:  # can't delete an already deleted data
        j.sal.fs.getDirName(long_file_path, levelsUp=10)
    ex = cm.exception

    assert ("Cannot find part of dir 10 levels up, path %s" % long_file_path) in str(ex.args[0])

    path = j.sal.fs.getDirName(long_file_path, levelsUp=0)
    assert not path is None and path != ""
    path = j.sal.fs.getDirName(sandbox_path)
    assert path == "//"
    path = j.sal.fs.getDirName(sandbox_path2)
    assert path == "//"
    path = j.sal.fs.getDirName(long_file_path, lastOnly=True)
    assert path == "cloud"
    path = j.sal.fs.getDirName(long_file_path, levelsUp=3)
    assert path == "specs"

    print("TEST pathParse")
    # parse /sandbox path. should be ok
    res = j.sal.fs.pathParse(sandbox_path)
    print(res)
    assert len(res) == 4
    assert res[0] == "/sandbox/"
    assert res[1] == ""
    assert res[2] == ""
    assert res[3] == 0

    # parse /sandbox path existCheck = false
    # we can't determine if the path is a file or directory path
    # because the decorator will remove the trailing`/`
    # so by default I will treat it as a file pat
    res = j.sal.fs.pathParse(sandbox_path, existCheck=False)
    print(res)
    assert len(res) == 4
    assert res[0] == "/"
    assert res[1] == "sandbox"
    assert res[2] == ""
    assert res[3] == 0

    res = j.sal.fs.pathParse(inexistant_dir_path, existCheck=False)
    print(res)
    assert len(res) == 4
    assert res[0] == "/64ds6d4s67f6d7f6sd4f6s4/"
    assert res[1] == "Fsdfsdgjhgsdjfgsj"
    assert res[2] == ""
    assert res[3] == 0

    res = j.sal.fs.pathParse(inexistant_file_path, existCheck=False)
    print(res)
    assert len(res) == 4
    assert res[0] == "/64ds6d4s67f6d7f6sd4f6s4/Fsdfsdgjhgsdjfgsj/"
    assert res[1] == "yolo"
    assert res[2] == "bmat"
    assert res[3] == str(42)

    # parse  non-existing path with existCheck=False.
    res = j.sal.fs.pathParse(prio_path, existCheck=False)
    print(res)
    assert res[0] == "/root/tmp/"
    assert res[1] == "adoc"
    assert res[2] == "doc"
    assert res[3] == str(33)

    res = j.sal.fs.pathParse(sandbox_path + "/test", existCheck=False)
    print(res)
    assert res[0] == "/sandbox/"
    assert res[1] == "test"
    assert res[2] == ""
    assert res[3] == 0

    # if basedir specified that part of path will be removed
    res = j.sal.fs.pathParse(
        "/opt/qbase3/apps/specs/myspecs/definitions/cloud/datacenter.txt",
        "/opt/qbase3/apps/specs/myspecs/",
        existCheck=False,
    )
    # should return a list of dirpath,filename,extension,priority
    print(res)
    assert res[0] == "definitions/cloud/"
    assert res[1] == "datacenter"
    assert res[2] == "txt"
    assert res[3] == 0

    res = j.sal.fs.pathParse(
        "/opt/qbase3/apps/specs/myspecs/definitions/cloud/datacenter.txt",
        "/opt/qbase3/apps/specs/myspecs",
        existCheck=False,
    )
    # should return a list of dirpath,filename,extension,priority
    print(res)
    assert res[0] == "definitions/cloud/"
    assert res[1] == "datacenter"
    assert res[2] == "txt"
    assert res[3] == 0

    res = j.sal.fs.pathParse("/sandbox/cfg/jumpscale_config.toml", baseDir="/sandbox/cfg")
    # should return a list of dirpath,filename,extension,priority
    print(res)
    assert res[0] == "/"
    assert res[1] == "jumpscale_config"
    assert res[2] == "toml"
    assert res[3] == 0
