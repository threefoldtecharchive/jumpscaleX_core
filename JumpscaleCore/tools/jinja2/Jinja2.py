from Jumpscale import j
import os
from jinja2 import Template, StrictUndefined


class Jinja2(j.baseclasses.object):
    """
    """

    __jslocation__ = "j.tools.jinja2"

    def _init(self, **kwargs):
        self._codegendir = j.core.tools.text_replace("{DIR_VAR}/codegen")

        #
        self.reset(destroyall=False)

    def reset(self, destroyall=True):
        """
        kosmos 'j.tools.jinja2.reset()'

        :param destroyall: all templates will be removed from disk
        :return:
        """
        self._path_to_contenthash = {}  # path remembers what the hash of content is
        self._hash_to_template = {}
        self._hash_to_codeobj = {}
        if destroyall:
            j.sal.fs.remove(self._codegendir)
        j.sal.fs.createDir(self._codegendir)

    def template_get(self, path=None, text=None, reload=False):
        """
        returns jinja2 template and will be cached

        param: reload, only relevant for path, when path exists and has been loaded before will not load again (only cached in memory)
        param: path location of the template
        param: text = text of the template
        """

        if path is not None and text is not None:
            raise j.exceptions.Base("can not specify path and text at same time")
        if path is None and text is None:
            raise j.exceptions.Base("need to specify path or text")

        md5 = None
        if path is not None:
            if reload == False and path in self._path_to_contenthash:
                md5 = self._path_to_contenthash[path]
            else:
                text = j.sal.fs.readFile(path)

        if md5 is None:
            md5 = j.data.hash.md5_string(text)

        if md5 not in self._hash_to_template:
            self._hash_to_template[md5] = Template(text, undefined=StrictUndefined)
            self._hash_to_template[md5].md5 = md5

        return self._hash_to_template[md5]

    def template_render(self, path=None, text=None, dest=None, reload=False, **args):
        """

        load the template, do not write back to the path
        render & return result as string

        :param path: to template (use path or text)
        :param text: text which is the template if path is not used
        :param dest: where to write the result, if not specified then will just return the rendered text
        :param reload, only relevant for path, when path exists and has been loaded before will not load again (only cached in memory)
        :param args: args which will be passed to the template engine
        :return:
        """

        # self._log_debug("template render:%s"%path)
        t = self.template_get(path=path, text=text, reload=reload)

        try:
            txt = t.render(**args)
        except Exception as e:
            self._log_error("template error in:%s" % path)
            raise j.exceptions.Base(e)

        if dest is None:
            return txt
        else:
            # self._log_debug("write template:%s on dest:%s"%(path,dest))
            j.sal.fs.createDir(j.sal.fs.getDirName(dest))
            j.sal.fs.writeFile(dest, txt)

    def code_python_render(self, obj_key=None, path=None, text=None, dest=None, objForHash=None, name=None, **args):
        """

        :param obj_key:  is name of function or class we need to evaluate when the code get's loaded
        :param objForHash: if not used then will use **args as basis for calculating if we need to render again,
               otherwise will use obj: objForHash
        :param path: path of the template (is path or text to be used)
        :param text: if not path used, text = is the text of the template (the content)
        :param dest: if not specified will be in j.dirs.VARDIR,"codegen",md5+".py" (md5 is md5 of template+msgpack of args)
                        or if name is specified will use the name  j.dirs.VARDIR,"codegen",name+".py
        :param args: arguments for the template (DIRS will be passed by default)
        :return:
        """

        if dest is not None and name is not None:
            raise j.exceptions.Base("cannot specify name & dest at same time")

        if "j" in args:
            args.pop("j")

        t = self.template_get(path=path, text=text)

        if objForHash:
            tohash = j.data.serializers.msgpack.dumps(objForHash) + t.md5.encode()
        else:
            name_for_hash = name or ""
            tohash = (
                j.data.serializers.msgpack.dumps(str(args)) + name_for_hash.encode() + t.md5.encode()
            )  # make sure we have unique identifier
        md5 = j.data.hash.md5_string(tohash)

        if md5 in self._hash_to_codeobj:
            return self._hash_to_codeobj[md5]

        dest_md5 = None
        if dest is None:
            if name is not None:
                name = name.lower()
                dest = "%s/%s.py" % (self._codegendir, name)
                dest_md5 = "%s/%s.md5" % (self._codegendir, name)
            else:
                dest = "%s/_%s.py" % (self._codegendir, md5)
                dest_md5 = None

        self._log_debug("python code render:%s" % (dest))

        render = False
        if dest_md5 is not None and j.sal.fs.exists(dest_md5) and j.sal.fs.exists(dest):
            md5_ondisk = j.sal.fs.readFile(dest_md5)
            if md5_ondisk != md5:
                render = True
        elif not j.sal.fs.exists(dest):
            render = True

        if True or render:  # TODO: need to be fixed
            BASENAME = j.tools.codeloader._basename(dest)
            # means has not been rendered yet lets do
            try:
                out = t.render(j=j, DIRS=j.dirs, BASENAME=BASENAME, **args)
            except Exception as e:  # THERE NEEDS TO BE A BETTER WAY, WHY DOES ERROR HANDLING NOT WORK HERE
                self._log_error("template error in:%s" % path)
                raise j.exceptions.Base(e)

            j.sal.fs.writeFile(dest, out)
            if dest_md5 is not None:
                j.sal.fs.writeFile(dest_md5, md5)  # remember the md5
        obj = j.tools.codeloader.load(obj_key=obj_key, path=dest, md5=md5)

        self._hash_to_codeobj[md5] = obj

        return self._hash_to_codeobj[md5]

    def file_render(self, path, write=True, dest=None, **args):
        """
        will read file, render & then overwrite the same file unless if dest given

        std arguments given to renderer:

        - DIRS - j.dirs

        if dest is noe then the source file will be overwritten

        """
        if j.sal.fs.getBaseName(path).startswith("_") or "__py" in path:
            if "__init__" not in path:
                raise j.exceptions.Base("cannot render path:%s" % path)
        C = self.template_render(path=path, DIRS=j.dirs, **args)
        if C is not None and write:
            if dest:
                path = dest
            j.sal.fs.writeFile(path, C)
        return C

    def dir_render(
        self,
        path,
        dest=None,
        recursive=True,
        filter=None,
        minmtime=None,
        maxmtime=None,
        depth=None,
        exclude=[],
        followSymlinks=False,
        listSymlinks=False,
        **args,
    ):

        if exclude == []:
            exclude = ["*.egg-info", "*.pyc", "*.bak", "*__pycache__*"]

        for item in j.sal.fs.listFilesInDir(
            path=path,
            recursive=recursive,
            filter=filter,
            minmtime=minmtime,
            maxmtime=maxmtime,
            depth=depth,
            exclude=exclude,
            followSymlinks=followSymlinks,
            listSymlinks=listSymlinks,
        ):
            if j.sal.fs.getBaseName(path).startswith("_") or "__py" in path:
                continue
            self.file_render(item, **args)

    def copy_dir_render(
        self,
        src,
        dest,
        overwriteFiles=False,
        filter=None,
        ignoredir=[],
        ignorefiles=[],
        reset=False,
        render=True,
        **args,
    ):
        """
        copy dir from src to dest
        use ignoredir & ignorefiles while copying
        filter is used where templates are applied on (will copy more in other words)

        example:

        src = j.clients.git.getContentPathFromURLorPath("https://github.com/threefoldtech/jumpscale_lib/tree/development/apps/example")
        dest = j.sal.fs.getTmpDirPath("jumpscale/jinja2test")
        self._log_info("copy templates to:%s"%dest)
        j.tools.jinja2.copy_dir_render(src,dest,j=j,name="aname")

        """
        if ignoredir == []:
            ignoredir = [".egg-info", ".dist-info"]
        if ignorefiles == []:
            ignorefiles = [".egg-info", ".pyc", ".bak"]

        if reset:
            j.sal.fs.remove(dest)

        j.sal.fs.createDir(dest)

        j.sal.fs.copyDirTree(
            src,
            dest,
            keepsymlinks=False,
            overwriteFiles=overwriteFiles,
            ignoredir=ignoredir,
            ignorefiles=ignorefiles,
            rsync=True,
            recursive=True,
            rsyncdelete=True,
            createdir=False,
        )

        if render:
            self.dir_render(path=dest, filter=filter, **args)

    def test(self):
        """
        kosmos 'j.tools.jinja2.test()'
        """
        raise j.exceptions.Base(
            "need to go to jumpscaleX something, also tests are really not tests, need to be better"
        )

        src = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldtech/jumpscale_lib/tree/development/apps/example"
        )
        dest = j.sal.fs.getTmpDirPath("jumpscale/jinja2test")
        self._log_info("copy templates to:%s" % dest)
        j.tools.jinja2.copy_dir_render(src, dest, j=j, name="aname")

        self.test_performance()

    def test_performance(self):
        """
        kosmos 'j.tools.jinja2.test_performance()'
        """
        path = j.sal.fs.getDirName(os.path.abspath(__file__)) + "/test_class.py"
        j.tools.timer.start("jinja_code")
        nr = 1000
        obj = self.code_python_render(obj_key="MyClass", path=path, reload=True, name="name:%s" % 1)
        for x in range(nr):
            obj = self.code_python_render(obj_key="MyClass", path=path, reload=False, name="name:%s" % x)
        res = j.tools.timer.stop(nr)
        assert res > 500

        j.tools.timer.start("jinja_code2")  # here we open class which has already been rendered
        nr = 1000
        for x in range(nr):
            obj = self.code_python_render(
                obj_key="MyClass", path=path, reload=False, name="name:%s" % 1
            )  # now use same
        res = j.tools.timer.stop(nr)
        assert res > 5000

        C = """
        somedata = {{name}}
        somethingelse= {{j.data.time.epoch}}
        """

        j.tools.timer.start("jinja text")
        nr = 5000
        for x in range(nr):
            R = self.template_render(text=C, reload=False, j=j, name="myname:%s" % x)
        res = j.tools.timer.stop(nr)
        assert res > 10000

        self.reset()
