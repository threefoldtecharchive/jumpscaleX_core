import calendar
import time

from datetime import datetime
from Jumpscale import j

JSBASE = j.baseclasses.object

import os
import time
import errno


class FileLockException(Exception):
    pass


class FileLock(object):
    """ A file locking mechanism that has context-manager support so
        you can use it in a with statement. This should be relatively cross
        compatible as it doesn't rely on msvcrt or fcntl for the locking.
    """

    def __init__(self, file_name):
        """ Prepare the file locker. Specify the file to lock and optionally
            the maximum timeout and the delay between each attempt to lock.
        """
        self.file_name = file_name
        self.delay = 0.1
        self.fd = None

    @property
    def locked(self):
        return j.sal.fs.exists(self.file_name)

    def acquire(self, timeout=None):
        """ Acquire the lock, if possible. If the lock is in use, it check again
            every `wait` seconds. It does this until it either gets the lock or
            exceeds `timeout` number of seconds, in which case it throws
            an exception.
        """
        start_time = time.time()
        while True:
            if self.locked:
                if timeout is None:
                    raise FileLockException("Could not acquire lock on {}".format(self.file_name))
                if (time.time() - start_time) >= timeout:
                    raise FileLockException("Timeout occured.")
            else:
                self.fd = os.open(self.file_name, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return
            time.sleep(self.delay)

    def release(self):
        """ Get rid of the lock by deleting the lockfile.
            When working in a `with` statement, this gets automatically
            called at the end.
        """
        if self.fd and self.locked:
            os.close(self.fd)
        j.sal.fs.remove(self.file_name)

    def __del__(self):
        """ Make sure that the FileLock instance doesn't leave a lockfile
            lying around.
        """
        self.release()

    def __exit__(self):
        self.release()


class FileLockFactory(j.baseclasses.object):
    __jslocation__ = "j.tools.filelock"

    def lock_get(self, file_name):
        return FileLock(file_name=file_name)

    def test(self):
        """
        kosmos 'j.tools.filelock.test()'
        """
        l = j.tools.filelock.lock_get("/tmp/test_lock")
        l.release()
        l.acquire()
        assert l.locked == True
        l.release()
        assert l.locked == False
