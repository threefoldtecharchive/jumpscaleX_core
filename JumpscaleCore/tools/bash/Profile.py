from Jumpscale import j
import re
import os
from io import StringIO
import locale


class Profile(j.baseclasses.object):
    _env_pattern = re.compile(r"([A-Za-z0-9_]+)=(.*)\n", re.MULTILINE)
    _include_pattern = re.compile(r"(source|\.) (.*)$", re.MULTILINE)

    def __init__(self, bash, profile_path=None):
        """
        X="value"
        Y="value"
        PATH="p1:p2:p3"

        export X
        export Y
        """
        j.baseclasses.object.__init__(self)
        self.bash = bash
        self.executor = bash.executor
        self.profile_path = profile_path
        self.state = "home"
        self.load()

    def _env_vars_find(self, content):
        """get defined environment variables in `content`
        this will match for XYZ=value

        :param content: content of e.g. a bash profile or the output of `printenv`
        :type content: str
        :return: a mapping between variables/values
        :rtype: dict
        """
        return dict(self._env_pattern.findall(content))

    def _includes_find(self, content):
        """get included sources
        this will match for `source file.sh` or `. file.sh`

        :param content: content of e.g. bash profile
        :type content: str
        :return: a list of included files
        :rtype: list of str
        """
        return [match.group(2) for match in self._include_pattern.finditer(content)]

    def _quote(self, value):
        value = value.strip('"').strip().strip('"')
        return '"%s"' % value

    def load(self):
        self._env = {}
        self._includes = []

        if not self.executor.exists(self.profile_path):
            self.executor.file_write(self.profile_path, "")
            return

        # to let bash evaluate the profile source, we source the profile
        # then get the current environment variables using printenv
        _, current_env, _ = self.executor.execute("source %s && printenv" % self.profile_path)

        # get a set of profile variables and current environment variables
        content = self.executor.file_read(self.profile_path)
        profile_vars = self._env_vars_find(content)
        current_env = self._env_vars_find(current_env)
        for var, value in current_env.items():
            if var in profile_vars:
                # only get the evaluated value from current env
                # if it's already in current profile
                self._env[var] = self._quote(value)

        # includes
        self._includes.extend(self._includes_find(content))

    def _path_clean(self, path):
        path = path.strip()
        path = path.replace("//", "/")
        path = path.replace("//", "/")
        path = path.rstrip("/")
        path = path.replace(";", ":")
        return path

    def path_add(self, path, end=False, check_exists=True, save=True):
        """
        :param path:
        :return:
        """
        if check_exists and not j.sal.fs.exists(path):
            return
        self.env_set_part("PATH", self._path_clean(path), end=end, quote=True, save=save)

    def path_delete(self, path):
        """
        :param path:
        :return:
        """
        self.env_delete_part("PATH", self._path_clean(path))

    @property
    def paths(self):
        return self.env_get_parts("PATH")

    def include_add(self, path):
        path = self._path_clean(path)
        if path not in self._includes:
            self._includes.append(path)
            self._save()

    def env_set(self, key, value, save=True, quote=False):
        if quote:
            value = self._quote(value)

        self._env[key] = value
        if save:
            self._save()

    def env_set_part(self, key, value, end=False, quote=False, save=True, separator=":"):
        """
        will check that there are no double entries in the environment variable
        env parts are separated by : or ;
        :param key:
        :param value:
        :param quote: means will put '' around env parts if space in the item
        :param end, put at end of line or start
        :return:
        """
        value = j.data.types.string.clean(value).strip().strip("'").strip('"').strip()

        if key in self._env:
            line = self._env[key].strip().strip("'").strip('"').strip()
            if separator is ";" and ":" in line:
                raise j.exceptions.Input(
                    "cannot have 2 separators, should be %s, %s in %s" % (separator, line, self.profile_path)
                )
            elif separator is ":" and ";" in line:
                raise j.exceptions.Input(
                    "cannot have 2 separators, should be %s, %s in %s" % (separator, line, self.profile_path)
                )
            items0 = [i.strip().strip("'").strip('"').strip() for i in line.split(separator)]
            items = []
            for i in items0:
                if i not in items:
                    items.append(i)

            if value in items:
                items.pop(items.index(value))

            if quote and " " in value:
                value = self._quote(value)
            if end:
                items.append(value.strip())
            else:
                items.insert(0, value.strip())
            self.env_set(key, separator.join(items).strip(separator), save=save)
        else:
            self.env_set(key, value, save=save)

    def env_get_parts(self, key):

        if key in self._env:
            line = self._env[key]
            if ":" in line:
                sep = ":"
            elif ";" in line:
                sep = ";"
            else:
                sep = None
            if sep:
                items = [i.strip() for i in line.split(sep)]
                return items
            else:
                return [line.strip()]
        else:
            return []

    def env_get(self, key):
        return self._env[key]

    def env_exists(self, key):
        return key in self._env

    def env_exists_part(self, key, value):
        return value.strip() in self.env_get_parts(key)

    def env_delete_part(self, key, value):
        """
        remove a part from an env part
        env parts are separated by : or ;
        :param key:
        :param value:
        :return:
        """
        value = j.data.types.string.clean(value).strip().strip("'").strip('"').strip()
        sep = ":"
        value = value.strip()
        if key in self._env:
            line = self._env[key].strip().strip("'").strip('"').strip()
            items = [i.strip().strip("'").strip('"').strip() for i in line.split(sep)]
            if value in items:
                items.pop(items.index(value))
                self.env_set(key, sep.join(items).strip(sep))

    def env_delete(self, key):
        if self.env_exists(key):
            del self._env[key]
            self._save()

    def delete(self):
        self.executor.file_write(self.profile_path, "")
        self.load()

    @property
    def env(self):
        return self._env

    def replace(self, text):
        """
        will look for $ENVNAME 's and replace them in text
        """
        for key, val in self.env.items():
            text = text.replace("$%s" % key, val)
        return text

    def _save(self):
        """
        save to disk
        """

        if "PATH" in self.env:
            self.path_add("/bin", end=True, check_exists=True, save=False)
            self.path_add("/sbin", end=True, check_exists=True, save=False)
            self.path_add("/usr/bin", end=True, check_exists=True, save=False)
            self.path_add("/usr/sbin", end=True, check_exists=True, save=False)
            self.path_add("/usr/local/bin", end=True, check_exists=True, save=False)
            self.path_add("/usr/local/sbin", end=True, check_exists=True, save=False)

        if j.core.tools.text_replace(self.profile_path).lower() == "/sandbox/env.sh":
            raise j.exceptions.JSBUG("should never overwrite /sandbox/env.sh")

        self.executor.file_write(self.profile_path, str(self))

    def locale_items_get(self, force=False, showout=False):

        if self.executor.type == "local":
            return [item for key, item in locale.locale_alias.items()]
        else:
            out = self.executor.execute("locale -a")[1]
            return out.split("\n")

    def locale_check(self):
        """
        return true of locale is properly set
        """
        if j.core.platformtype.myplatform.platform_is_osx:
            a = self.bash.env.get("LC_ALL") == "en_US.UTF-8"
            b = self.bash.env.get("LANG") == "en_US.UTF-8"
        else:
            a = self.bash.env.get("LC_ALL") == "C.UTF-8"
            b = self.bash.env.get("LANG") == "C.UTF-8"
        if (a and b) != True:
            self._log_debug("WARNING: locale has been fixed, please do: " "`source ~/.profile_js`")
            self.locale_fix()
            self._save()

    def locale_fix(self, reset=False):
        items = self.locale_items_get()
        self.env_set("TERMINFO", "xterm-256colors")
        if "en_US.UTF-8" in items or "en_US.utf8" in items:
            self.env_set("LC_ALL", "en_US.UTF-8")
            self.env_set("LANG", "en_US.UTF-8")
            return
        elif "C.UTF-8" in items or "c.utf8" in items:
            self.env_set("LC_ALL", "C.UTF-8")
            self.env_set("LANG", "C.UTF-8")
            return
        raise j.exceptions.Input("Cannot find C.UTF-8, cannot fix locale's")

    def __str__(self):

        content = StringIO()
        content.write("# environment variables\n")
        for key, value in self._env.items():
            content.write("export %s=%s\n" % (key, value))

        content.write("# includes\n")
        for path in self._includes:
            if self.executor.exists(path):
                content.write("source %s\n" % path)

        return content.getvalue()

    __repr__ = __str__
