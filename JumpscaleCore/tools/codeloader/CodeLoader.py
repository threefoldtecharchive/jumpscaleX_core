from Jumpscale import j
import imp

JSBASE = j.baseclasses.object


class CodeLoader(j.baseclasses.object):
    """
    """

    __jslocation__ = "j.tools.codeloader"

    def _init(self, **kwargs):

        #
        j.sal.fs.createDir("%s/codegen" % j.dirs.VARDIR)
        self._hash_to_codeobj = {}

    def _basename(self, path):
        obj_key = j.sal.fs.getBaseName(path)
        if obj_key.endswith(".py"):
            obj_key = obj_key[:-3]
        if obj_key[0] in "0123456789":
            raise j.exceptions.Base("obj key cannot start with nr: now:'%s'" % obj_key)
        return obj_key

    def load_text(self, obj_key=None, text=None, dest=None, reload=False, md5=None):
        """

        write text as code file or in codegen location or specified dest
        load this text as code in mem (module python)
        get the objkey out of the code e.g. a method or a class

        :param obj_key:  is name of function or class we need to evaluate when the code get's loaded
        :param text: if not path used, text = is the text of the template (the content)
        :param dest: if not specified will be in j.dirs.VARDIR,"codegen",md5+".py" (md5 is md5 of template+msgpack of args)
        :param reload: will reload the template and re-render
        :return:
        """
        if md5 is None:
            md5 = j.data.hash.md5_string(text)
        if dest is None:
            dest = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", md5 + ".py")

        if reload or not j.sal.fs.exists(dest):
            j.sal.fs.writeFile(dest, text)

        return self.load(obj_key=obj_key, path=dest, reload=reload, md5=md5)

    def load(self, obj_key=None, path=None, reload=False, md5=None):
        """

        example:

        j.tools.codeloader.load(obj_key,path=path,reload=False)

        :param obj_key:  is name of function or class we need to evaluate when the code get's loaded
        :param path: path of the template (is path or text to be used)
        :param reload: will reload the template and re-render
        :return:
        """

        if not obj_key:
            obj_key = self._basename(path)

        if not j.data.types.string.check(path):
            raise j.exceptions.Base("path needs to be string")
        if path is not None and not j.sal.fs.exists(path):
            raise j.exceptions.Base("path:%s does not exist" % path)

        if md5 is None:
            txt = j.sal.fs.readFile(path)
            md5 = j.data.hash.md5_string(txt)

        if reload or md5 not in self._hash_to_codeobj:

            try:
                m = imp.load_source(name=md5, pathname=path)
            except Exception as e:
                out = j.sal.fs.readFile(path)
                msg = "SCRIPT CONTENT:\n%s\n\n" % out
                msg += "---------------------------------\n"
                msg += "COULD not load source:%s\n" % path
                msg += "ERROR WAS:%s\n\n" % e
                raise j.exceptions.Base(msg)
            try:
                obj = eval("m.%s" % obj_key)
            except Exception as e:
                out = j.sal.fs.readFile(path)
                msg = "SCRIPT CONTENT:\n%s\n\n" % out
                msg += "---------------------------------\n"
                msg += "ERROR:COULD not import source:%s\n" % path
                msg += "ERROR WAS:%s\n\n" % e
                msg += "obj_key:%s\n" % obj_key
                raise j.exceptions.Base(msg)

            self._hash_to_codeobj[md5] = obj

        return self._hash_to_codeobj[md5]
