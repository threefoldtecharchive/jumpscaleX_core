from Jumpscale import j

JSBASE = j.baseclasses.object

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import gipc


def monitor_changes_parent(gedis_instance_name):
    gipc.start_process(monitor_changes_subprocess, (gedis_instance_name,))


def monitor_changes_subprocess(gedis_instance_name,):
    """
    js_shell 'j.servers.rack.monitor_changes("test")'
    """
    import time

    print("log: init monitor fs")
    from watchdog.observers import Observer

    connected = False
    while not connected:
        try:
            time.sleep(2)
            cl = j.clients.gedis.get(gedis_instance_name)
            connected = True
        except Exception:
            connected = False

    print("log: gedis connected")

    event_handler = ChangeWatchdog(client=cl)
    observer = Observer()

    res = cl.system.filemonitor_paths()
    for source in res.paths:
        print("log: monitor:%s" % source)
        observer.schedule(event_handler, source, recursive=True)

    print("log: are now observing filesystem changes")

    observer.start()
    print("started")
    try:
        while True:
            time.sleep(2)
            print("filesystem monitor alive")
    except KeyboardInterrupt:
        pass


class ChangeWatchdog(FileSystemEventHandler, JSBASE):
    def __init__(self, client):
        JSBASE.__init__(self)
        self.client = client

    def handler(self, event, action=""):

        print("%s:%s" % (event, action))

        changedfile = event.src_path

        if changedfile.find("/.git/") != -1:
            return
        elif changedfile.find("/__pycache__/") != -1:
            return
        elif changedfile.endswith(".pyc"):
            return

        self.client.system.filemonitor_event(
            is_directory=event.is_directory, src_path=event.src_path, event_type=event.event_type
        )

    def on_any_event(self, event):
        self.handler(event, action="")

    # def on_moved(self, event):
    #     self.handler(event, action="")

    # def on_created(self, event):
    #     self.handler(event)

    # def on_deleted(self, event):
    #     self.handler(event, action="")

    # def on_modified(self, event):
    #     self.handler(event)
