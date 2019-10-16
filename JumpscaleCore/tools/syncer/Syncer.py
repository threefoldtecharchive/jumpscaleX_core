from Jumpscale import j
import time
from watchdog.observers import Observer
from .MyFileSystemEventHandler import MyFileSystemEventHandler
import gevent
from gevent import time
import traceback
import re


class Syncer(j.baseclasses.object_config):

    """
    make sure there is an ssh client first, can be done by

    j.clients.ssh.get...

    :param name:
    :param sshclient_name: name as used in j.clients.ssh
    :param paths: specified as
        e.g.  "{DIR_CODE}/github/threefoldtech/0-robot:{DIR_TEMP}/0-robot,..."
        e.g.  "{DIR_CODE}/github/threefoldtech/0-robot,..."
        can use the {} arguments
        if destination not specified then is same as source

    if not specified is:
        paths = "{DIR_CODE}/github/threefoldtech/jumpscaleX,{DIR_CODE}/github/threefoldtech/digitalmeX"

    """

    _SCHEMATEXT = """
        @url = jumpscale.syncer.1
        name** = "" (S)
        sshclient_names = [] (LS)
        paths = [] (LS)
        ignoredir = [] (LS)
        ignore_delete = true  (B)  
        rsyncdelete = false (B)
        """

    def sshclients_add(self, sshclients=None):
        """

        :param sshclients: name of sshclient, sshclient or list of sshclient or names
        :return:
        """
        assert sshclients
        from Jumpscale.clients.ssh.SSHClientBase import SSHClientBase

        if j.data.types.list.check(sshclients):
            for item in sshclients:
                self.sshclients_add(item)
            return
        elif isinstance(sshclients, SSHClientBase):
            cl = sshclients
        elif isinstance(sshclients, str):
            name = sshclients
            if not j.clients.ssh.exists(name=name):
                raise j.exceptions.Base("cannot find sshclient:%s for syncer:%s" % (name, self))

            cl = j.clients.ssh.get(name=name)
        else:
            raise j.exceptions.Base("only support name of sshclient or the sshclient instance itself")

        if cl.name not in self.sshclients:
            self.sshclients[cl.name] = cl
            if not cl.name in self.sshclient_names:
                self.sshclient_names.append(cl.name)
                self.save()

    def _init(self, **kwargs):

        self.sshclients = {}
        self._monitor = None

        for name in self.sshclient_names:
            self.sshclients_add(name)

        self.IGNOREDIR = [".git", ".github"]
        self._executor = None

        self._log_info("syncer started")

        if self.paths == []:
            for item in [
                "jumpscaleX_builders",
                "jumpscaleX_core/",
                "jumpscaleX_libs",
                "jumpscaleX_libs_extra",
                "jumpscaleX_threebot",
            ]:
                self.paths.append("{DIR_CODE}/github/threefoldtech/%s" % item)
            self.save()

    def _get_paths(self, executor=None):
        """
        :return: [[src,dest],...]
        """
        res = []
        for item in self.paths:

            if not item.startswith("/") and not item.startswith("{"):
                item = j.sal.fs.getcwd() + "/" + item
            item = item.replace("//", "/")

            items = item.split(":")
            if len(items) == 1:
                src = items[0]
                dst = src
            elif len(items) == 2:
                src = items[0]
                dst = items[1]
            else:
                raise j.exceptions.Base("can only have 2 parts")
            src = j.core.tools.text_replace(src)
            if not executor:
                dst = None
            else:
                if "{" in dst:
                    dst = executor._replace(dst)
            res.append((src, dst))
        return res

    def _path_dest_get(self, executor=None, src=None):
        assert executor
        assert src
        for src_model, dest_model in self._get_paths(executor=executor):
            if src.startswith(src_model):
                dest = j.sal.fs.joinPaths(dest_model, j.sal.fs.pathRemoveDirPart(src, src_model))
                return dest
        raise j.exceptions.Base("did not find:%s" % src)

    def monitor(self):
        from .MyFileSystemEventHandler import FileSystemMonitor

        self._monitor = FileSystemMonitor(syncer=self)
        print("the only way how it works today, don't ask me why:")
        print("if your ssh connection is called 'master'")
        print("kosmos -p")
        print("then in shell do: 'j.clients.ssh.master.syncer.sync()'")
        self._monitor.start()
        print("monitor started, are out of loop")
        time.sleep(3600)

    def handler(self, event, action="copy"):
        self._log_info("......................new event........................")
        self._log_info("syncer handle")
        self._log_info("event:%s" % event)
        self._log_info("action:%s" % action)
        self._log_debug("%s:%s" % (event, action))
        for key, sshclient in self.sshclients.items():
            if sshclient.executor.isContainer:
                continue
            changedfile = event.src_path
            if event.src_path.endswith((".swp", ".swx")):
                return
            elif event.is_directory:
                if changedfile.find("/.git") != -1:
                    return
                elif changedfile.find("/__pycache__/") != -1:
                    return
                elif changedfile.find(".egg-info") != -1:
                    return
                if event.event_type == "modified":
                    return
                self._log_info("directory changed")
                return self.sync(monitor=False)  # no need to continue
            else:
                self._log_info("changed file name: %s" % changedfile)
                if changedfile.find("/.git") != -1:
                    return
                elif changedfile.find("/__pycache__/") != -1:
                    return
                elif changedfile.find("/_tmp_/") != -1:
                    return
                elif changedfile.endswith(".pyc"):
                    return
                elif changedfile.endswith("___"):
                    return
                elif changedfile.endswith("~"):
                    return
                elif hasattr(event, "dest_path"):
                    if event.dest_path.endswith("~"):
                        return
                dest = self._path_dest_get(executor=sshclient.executor, src=changedfile)
                self._log_info("destination file name: %s" % dest)

                e = ""
                self._log_debug("action:%s for %s" % (action, changedfile))

                rc = 1
                counter = 0
                while rc == 1 and counter < 10:
                    counter += 1
                    if action == "copy":
                        self._log_info("copy (ssh:%s): %s:%s" % (sshclient.name, changedfile, dest))
                        try:
                            sshclient.file_copy(changedfile, dest)
                            rc = 0
                            self._log_info("OK")
                        except Exception as e:
                            j.shell()
                            if str(e).find("SocketSendError") != -1:
                                rc = 1
                                continue
                            else:
                                rc = 2
                                break
                    elif action == "delete":
                        self._log_debug("delete: %s:%s" % (changedfile, dest))
                        try:
                            cmd = "rm -f %s" % dest
                            sshclient.execute(cmd)
                            rc = 0
                            self._log_info("OK")
                        except Exception as e:
                            self._log_error("Couldn't remove file: %s" % (dest))
                            if "No such file" in str(e):
                                rc = 0
                                continue
                            else:
                                rc = 1
                                continue
                    elif action == "moved":
                        self._log_debug("moving  : %s:%s" % (changedfile, event.dest_path))
                        try:
                            cmd = "mv  %s %s" % (changedfile, event.dest_path)
                            sshclient.execute(cmd)
                            rc = 0
                            self._log_info("OK")
                        except Exception as e:
                            self._log_error("Couldn't move file: %s" % (event.dest_path))
                            if "No such file" in str(e):
                                rc = 0
                                continue
                            else:
                                rc = 1
                                continue
                    else:
                        raise j.exceptions.JSBUG("action not understood in filesystemhandler on sync:%s" % action)

                if rc > 0:
                    self._log_error("Couldn't sync file: %s:%s" % (changedfile, dest))
                    self._log_error("** ERROR HAPPENED, WILL SYNC ALL")
                    try:
                        self._log_error(str(e))
                    except:
                        pass  # no idea why we need to do this, but e not known
                    return self.sync(monitor=False)

    def delete(self):
        for item in j.clients.ssh.find(name=self.sshclient_name):
            item.delete()
        j.baseclasses.object_config.delete(self)

    def sync(self, monitor=True):
        """
        sync all code to the remote destinations, uses config as set in jumpscale.toml

        """

        for key, sshclient in self.sshclients.items():

            if sshclient.executor.isContainer:
                continue

            for item in self._get_paths(executor=sshclient.executor):
                source, dest = item
                self._log_info("upload:%s to %s" % (source, dest))
                sshclient.executor.upload(
                    source,
                    dest,
                    recursive=True,
                    createdir=True,
                    rsyncdelete=self.rsyncdelete,
                    ignoredir=self.IGNOREDIR,
                    ignorefiles=None,
                    retry=10,
                )

        if monitor:
            self.monitor()
