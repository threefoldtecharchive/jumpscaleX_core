from Jumpscale import j
from pprint import pprint as print

JSBASE = j.baseclasses.object


class IndexFile(j.baseclasses.object):
    def __init__(self, path, nrbytes=4):
        j.sal.fs.createDir(j.sal.fs.getDirName(path))
        self._path = path
        self._nrbytes = nrbytes
        if j.sal.fs.exists(path):
            self._f = open(path, mode="rb+")
        else:
            self._f = open(path, mode="wb+")
        JSBASE.__init__(self)

    def __delete__(self):
        self.close()

    def close(self):
        if self._f:
            self._f.close()

    @property
    def nrbytes(self):
        return self._nrbytes

    @property
    def path(self):
        return self._path

    @property
    def count(self):
        """
        return the number of entry in the index
        """
        size = self._f.seek(0, 2)
        if size % self.nrbytes != 0:
            raise j.exceptions.RuntimeError("size of the file is not a multiple of nbrbytes, file corrupted")
        return int(size / self.nrbytes)

    def _offset(self, id):
        """
        compute the offset into the index
        """
        return id * self.nrbytes

    def _encode(self, item):
        if isinstance(item, str):
            item = item.encode("utf-8")
        return item

    def get(self, id):
        """
        return the data stored at id=id
        """
        self._f.seek(self._offset(id))
        data = self._f.read(self.nrbytes)
        return data

    def set(self, id, data):
        """
        store a data at index id
        """
        data = self._encode(data)

        if len(data) != self.nrbytes:
            raise j.exceptions.Input("the size of pos needs to be %d not %d" % (self.nrbytes, len(data)))

        self._f.seek(self._offset(id))
        self._f.write(data)

    def iterate(self, method, start=None, end=None, result=None):
        """walk over the indexfile and apply method as follows

        call for each item:
            '''
            for each:
                result = method(id,data,result)
            '''
        result is the result of the previous call to the method

        Arguments:
            method {python method} -- will be called for each item found in the file

        Keyword Arguments:
            start {int} -- start id (default: {0})
            end {int} -- end id (default: {0}, which means end of file)
        """
        if start is not None:
            id = start
        else:
            id = 0

        self._f.seek(self._offset(id))

        while True:
            data = self._f.read(self.nrbytes)
            if len(data) < self.nrbytes:
                break  # EOF
            result = method(id, data, result=result)
            id += 1
            if end is not None and id > end:
                break

        return result

    def list(self, start=None, end=None):
        result = {}

        def do(id, data, result):
            # print("id:%s:%s"%(id,data))
            result[id] = data
            return result

        result = self.iterate(do, start=start, end=end, result={})
        return result
