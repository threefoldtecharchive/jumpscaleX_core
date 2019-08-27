from Jumpscale import j

# from pprint import pprint as print

from .IndexFile import IndexFile

JSBASE = j.baseclasses.object


class IndexDB(j.baseclasses.object):
    __jslocation__ = "j.data.indexfile"

    def _init(self, **kwargs):
        self.basepath = "%s/indexfile/" % (j.dirs.VARDIR)

    def get(self, name, path=None, nrbytes=4):
        if path is None:
            path = j.sal.fs.joinPaths(self.basepath, name.lower().strip())

        return IndexFile(path, nrbytes=nrbytes)

    def test(self):
        """
        kosmos 'j.data.indexfile.test()'

        """
        # test set
        index = self.get("test")
        for i in range(10):
            data = str(i) * index.nrbytes
            index.set(i, data)

        assert index.count == 10

        assert index.list(0, 0) == {0: b"0000"}
        assert index.list(0, 1) == {0: b"0000", 1: b"1111"}
        assert index.list(1, 1) == {1: b"1111"}

        assert index.list() == {
            0: b"0000",
            1: b"1111",
            2: b"2222",
            3: b"3333",
            4: b"4444",
            5: b"5555",
            6: b"6666",
            7: b"7777",
            8: b"8888",
            9: b"9999",
        }

        try:
            index.set(11, b"data too long")
            assert False
        except j.exceptions.Input:
            # should raise
            pass

            # test get
        for i in range(10):
            expected = (str(i) * index.nrbytes).encode()
            actual = index.get(i)
            assert expected == actual

        # test iterate over all
        actual = []

        def walk(pos, data, result):
            actual.append(data)

        index.iterate(walk, None, None)
        expected = []
        for i in range(10):
            expected.append((str(i) * index.nrbytes).encode())
        print("expected:", expected)
        print("actual:  ", actual)
        assert expected == actual

        # test iterate over a portion
        actual = []

        def walk(pos, data, result):
            actual.append(data)

        index.iterate(walk, 4, 9)
        expected = []
        for i in range(4, 9 + 1):
            expected.append((str(i) * index.nrbytes).encode())
        print("expected:", expected)
        print("actual:  ", actual)
        assert expected == actual

        j.sal.fs.remove(index.path)
