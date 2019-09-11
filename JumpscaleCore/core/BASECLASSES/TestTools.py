# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/
# In case TF TECH NV ceases to exist (e.g. because of bankruptcy)
#   then Incubaid NV also in Belgium will get the Copyright & Authorship for all changes made since July 2018
#   and the license will automatically become Apache v2 for all code related to Jumpscale & DigitalMe
# This file is part of jumpscale at <https://github.com/threefoldtech>.
# jumpscale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jumpscale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License v3 for more details.
#
# You should have received a copy of the GNU General Public License
# along with jumpscale or jumpscale derived works.  If not, see <http://www.gnu.org/licenses/>.
# LICENSE END


from Jumpscale import j
import re

"""
adds test management to JSBASE
"""


class TestTools:

    #### TESTING FUNCTIONALITY

    def _test_error(self, name, error):
        j.errorhandler.try_except_error_process(error, die=False)
        self.__class__._test_runs_error[name] = error

    def _test_run(self, name="", obj_key="main", die=True, **kwargs):
        """

        :param name: name of file to execute can be e.g. 10_test_my.py or 10_test_my or subtests/test1.py
                    the tests are found in subdir tests of this file

                if empty then will use all files sorted in tests subdir, but will not go in subdirs

        :param obj_key: is the name of the function we will look for to execute, cannot have arguments
               to pass arguments to the example script, use the templating feature, std = main


        :return: result of the tests

        """

        res = self.__test_run(name=name, obj_key=obj_key, die=die, **kwargs)
        if self.__class__._test_runs_error != {}:
            for key, e in self.__class__._test_runs_error.items():
                self._log_error("ERROR FOR TEST: %s\n%s" % (key, e))
            self._log_error("SOME TESTS DIT NOT COMPLETE SUCCESFULLY")
        else:
            self._log_info("ALL TESTS OK")
        return res

    def _code_run(self, path, name=None, obj_key="main", die=True, **kwargs):
        if not path.startswith("/"):
            path2 = self._dirpath + "/" + path
        else:
            path2 = path
        assert j.sal.fs.exists(path2)
        if j.sal.fs.isDir(path2):
            path3 = self.__find_code(name=name, path=path2)
        else:
            path3 = path2
        method = j.tools.codeloader.load(obj_key=obj_key, path=path3)
        self._log_debug("##:LOAD: path: %s\n\n" % path2)
        if die or j.application.debug:
            res = method(self=self, **kwargs)
        else:
            try:
                res = method(self=self, **kwargs)
            except Exception as e:
                if j.application.debug:
                    raise e
                else:
                    j.errorhandler.try_except_error_process(e, die=False)
                # self.__class__._test_runs_error[name] = e
                return e
            # self.__class__._test_runs[name] = res
        return res

    def __find_code(self, name, path="tests", recursive=True):

        if not path.startswith("/"):
            path = self._dirpath + "/" + path
        assert j.sal.fs.exists(path)

        def get_shortname(bname, underscoreprocess=True):
            # self._log_debug(bname)
            if underscoreprocess:
                if "_" in bname:
                    bname = bname.split("_", 1)[1]
            if bname.endswith(".py"):
                bname = bname[:-3]
            # self._log_debug(bname)
            return bname.lower()

        # we should test whitout underscore process first
        # to avoid taking twice the same file if it ends by the same prefix
        # e.g. base and x_base
        files = j.sal.fs.listFilesInDir(path, recursive=recursive, filter="*.py")
        if isinstance(name, int):
            matches = []
            for file in files:
                basename = j.sal.fs.getBaseName(file).split("_", 1)[0]
                if basename.isdigit() and int(basename) == name:
                    matches.append(file)
            if matches:
                return matches
            else:
                raise j.exceptions.NotFound(f"Could not find test with nr {name}")

        files_dict = {get_shortname(j.sal.fs.getBaseName(f)): f for f in files}
        target_file_shortened = get_shortname(name, underscoreprocess=False)
        if target_file_shortened in files_dict:
            return files_dict[target_file_shortened]
        else:
            target_file_shortened_no_underscore = get_shortname(name, underscoreprocess=True)
            if target_file_shortened_no_underscore in files_dict:
                return files_dict[target_file_shortened_no_underscore]

        """ j.shell()
        for item in j.sal.fs.listFilesInDir(path, recursive=recursive, filter="*.py"):
            bname = j.sal.fs.getBaseName(item)
            bname2 = get_shortname(bname)
            self._log_debug("%s:%s" % (bname2, name))
            
            if bname2 == get_shortname(name, underscoreprocess=False):
                return item
            if bname2 == get_shortname(name, underscoreprocess=True):
                return item """
        raise j.exceptions.Base("Could not find code: '%s' in %s" % (name, path))

    def __test_run(self, name=None, obj_key="main", die=True, **kwargs):

        if name == "":
            name = None

        if name is not None:
            self._log_info(f"##: TEST RUN: {name}")

        if name is not None:
            tpath = self.__find_code(name=name)
            if not isinstance(tpath, list):
                tpath = [tpath]
            for path in tpath:
                self._code_run(name=name, path=path, obj_key=obj_key, die=die, **kwargs)
                self._log_debug("##: path: %s\n\n" % path)
        else:
            items = [
                j.sal.fs.getBaseName(item)
                for item in j.sal.fs.listFilesInDir("%s/tests" % self._dirpath, recursive=False, filter="*.py")
            ]

            natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split("(\d+)", s)]
            items.sort(key=natsort)
            for name in items:
                self.__test_run(name=name, obj_key=obj_key, **kwargs)

            return
