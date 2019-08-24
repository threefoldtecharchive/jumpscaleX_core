from Jumpscale import j

JSBASE = j.baseclasses.object


from watchdog.events import FileSystemEventHandler

# from watchdog.events import LoggingEventHandler
from watchdog.observers import Observer
from watchdog.observers.fsevents import *
import time

# from gevent import Greenlet
# import gevent
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
    def __init__(self, syncer=None):
        self.syncer = syncer
        self.event_handler = MyFileSystemEventHandler(syncer=self.syncer)
        self.observer = Observer()

    def _log_info(self, msg):
        print(" - %s" % msg)

    def start(self):

        for item in self.syncer._get_paths():
            source, dest = item
            self._log_info("monitor:%s" % source)
            self.observer.schedule(self.event_handler, source, recursive=True)

        self.observer.start()

        self._log_info("WE ARE MONITORING")

        # try:
        #     while True:
        #         time.sleep(1)
        # except KeyboardInterrupt:
        #     pass

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
        self._log_info("event:%s" % event)
        if self._period != 0 and action == "copy":
            self._cleanup_done()
            if event.src_path in self._done:
                return
            self._done[event.src_path] = j.data.time.epoch
        self.syncer.handler(event, action=action)

    def _on_modified(self, event):
        self.handler(event, action="copy")

    def on_any_event(self, event):
        if isinstance(event, FileModifiedEvent):
            self.handler(event, action="copy")
        elif isinstance(event, DirModifiedEvent):
            return
        self._log_debug(event)

    def on_moved(self, event):
        self.syncer.sync(monitor=False)
        self.handler(event, action="moved")

    def on_created(self, event):
        self.handler(event, action="copy")

    def on_deleted(self, event):
        self.handler(event, action="delete")
