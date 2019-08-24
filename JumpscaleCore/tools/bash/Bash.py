from Jumpscale import j
from .Profile import Profile


class Bash(object):
    def __init__(self, path=None, profile_name=None, executor=None):
        """
        :param path: if None then will be '~' = Home dir
        :param executor:
        :param profile_name: if None will look for env.sh, .profile_js in this order
        """
        self._executor = executor

        if not path:
            self.path = j.dirs.HOMEDIR
        else:
            self.path = path

        if not profile_name:
            for i in ["env.sh", ".profile_js"]:
                if j.sal.fs.exists(j.sal.fs.joinPaths(self.path, i)):
                    profile_name = i
                    break

        if not profile_name:
            profile_name = "env.sh"

        profile_path = j.sal.fs.joinPaths(self.path, profile_name)

        self.profile = Profile(self, profile_path)

        # self.reset()

    @property
    def executor(self):
        if self._executor is None:
            self.executor = j.tools.executorLocal
        return self._executor

    @executor.setter
    def executor(self, newexecutor):
        self._executor = newexecutor

    def reset(self):
        self.executor.reset()

    @property
    def env(self):
        dest = dict(self.profile.env)
        dest.update(self.executor.env)
        return dest

    def cmd_path_get(self, cmd, die=True):
        """
        checks cmd Exists and returns the path
        """
        rc, out, err = self.executor.execute("source %s;which %s" % (self.profile.paths, cmd), die=False, showout=False)
        if rc > 0:
            if die:
                raise j.exceptions.RuntimeError("Did not find command: %s" % cmd)
            else:
                return False

        out = out.strip()
        if out == "":
            raise j.exceptions.Base("did not find cmd:%s" % cmd)

        return out
