from Jumpscale import j

JSBASE = j.baseclasses.object
from gevent import monkey

# monkey.patch_all()
monkey.patch_time()

from watchdog.events import FileSystemEventHandler, FileModifiedEvent, DirModifiedEvent

# from watchdog.events import LoggingEventHandler
# from watchdog.observers import Observer
from watchdog_gevent import Observer

# import time
from watchdog.events import FileModifiedEvent, DirModifiedEvent

# from gevent import Greenlet
import gevent

#
#
# class FileSystemMonitor(Greenlet):
#     def __init__(self, syncer):
#         Greenlet.__init__(self)
#         # JSBASE.__init__(self)
#         self.syncer = syncer
#         self.event_handler = MyFileSystemEventHandler(syncer=self.syncer)
#         self.observer = Observer()
#
#     def _log_info(self, msg):
#         print("* %s" % msg)
#
#     def _run(self):
#
#         for item in self.syncer._get_paths():
#             source, dest = item
#             self._log_info("monitor:%s" % source)
#             self.observer.schedule(self.event_handler, source, recursive=True)
#         self.observer.start()
#         self._log_info("WE ARE MONITORING")
#
#         while True:
#             gevent.sleep(10)
#
#     def __str__(self):
#         return "FileSystemMonitor"


class FileSystemMonitor:
    def __init__(self, syncer=None, minimal=True):
        self.syncer = syncer
        self.minimal = minimal
        self.event_handler = MyFileSystemEventHandler(syncer=self.syncer)
        self.observer = Observer(timeout=20)
        self.paths = []
        if minimal:
            self.paths_minimal()

    def _log_info(self, msg):
        print(" - %s" % msg)

    def paths_minimal(self):
        self.paths = []
        for item in [
            "jumpscaleX_core/JumpscaleCore",
            "jumpscaleX_core/cmds",
            "jumpscaleX_core/install",
            # "jumpscaleX_libs",
            # "jumpscaleX_threebot",
            # "jumpscaleX_builders",
            # "jumpscaleX_libs_extra",
            # "jumpscaleX_weblibs",
        ]:
            self.paths.append("{DIR_CODE}/github/threefoldtech/%s:/sandbox/code/github/threefoldtech/%s" % (item, item))

    def _get_paths(self):
        if self.paths != []:
            return self.syncer._get_paths(paths=self.paths)
        else:
            return self.syncer._get_paths()

    def start(self):

        for item in self._get_paths():
            source, dest = item
            self._log_info("monitor:%s" % source)
            self.observer.schedule(self.event_handler, source, recursive=True)

        self.observer.start()

        self._log_info("WE ARE MONITORING ")

        try:
            while True:
                gevent.time.sleep(1)
                # print(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    def __str__(self):
        return "FileSystemMonitor"


class MyFileSystemEventHandler(FileSystemEventHandler, JSBASE):
    def __init__(self, syncer=None):
        FileSystemEventHandler.__init__(self)
        JSBASE.__init__(self, syncer=syncer)

    def _init(self, syncer=None):
        assert syncer
        self.syncer = syncer
        self._done = {}
        self._period = 2

    def _cleanup_done(self):
        # remove all remembered paths older than 2 sec
        toremove = []
        for key, val in self._done.items():
            if val < j.data.time.epoch - self._period:
                toremove.append(key)
        for key in toremove:
            self._done.pop(key)

    def handler(self, event, action="copy"):
        """
        call all syncers
        :param event:
        :param action:
        :return:
        """
        # print("event:%s" % event)
        # self._log_info("event:%s" % event)
        if self._period != 0 and action == "copy":
            self._cleanup_done()
            if event.src_path in self._done:
                # self._log_info("the handles returned and didn't excute")
                return
            self._done[event.src_path] = j.data.time.epoch
        # self._log_info("the handles is going to excute")
        self.syncer.handler(event, action=action)

    def _on_modified(self, event):
        self.handler(event, action="copy")

    def on_any_event(self, event):
        if isinstance(event, FileModifiedEvent):
            self.handler(event, action="copy")
        elif isinstance(event, DirModifiedEvent):
            return
        # self._log_debug(event)

    def on_moved(self, event):
        self.syncer.sync(monitor=False)
        self.handler(event, action="moved")

    def on_created(self, event):
        self.handler(event, action="copy")

    def on_deleted(self, event):
        self.handler(event, action="delete")
