from Jumpscale import j

import os
from unittest import TestCase, skip

from parameterized import parameterized

locations_libs = []
locations_core = []
locations_threebot = []


class Tester:
    def _get_all_tests(locations, path):

        location_search = "__jslocation_"
        for root, dirs, files in os.walk(j.core.tools.text_replace(path)):
            for file in files:
                if file.endswith("Factory.py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r") as f:
                        content = f.read()
                    if location_search in content:
                        jslocation = content.find(location_search)
                        location = content[content.find("=", jslocation) + 1 : content.find("\n", jslocation)]
                        locations.append(location.strip().strip("'").strip('"'))


Tester._get_all_tests(locations_libs, "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_libs")
Tester._get_all_tests(locations_core, "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_core")
Tester._get_all_tests(locations_threebot, "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_threebot")


class TesterFactory(j.baseclasses.factory_testtools):
    __jslocation__ = "j.tools.tester"

    @parameterized.expand(locations_core)
    def test_core(self, location):
        module = eval(location)
        if "test" in dir(module):
            test = module.__getattribute__("test")
            test()

    @parameterized.expand(locations_libs)
    def test_libs(self, location):
        module = eval(location)
        if "test" in dir(module):
            test = module.__getattribute__("test")
            test()

    @parameterized.expand(locations_threebot)
    def test_threebot(self, location):
        module = eval(location)
        if "test" in dir(module):
            test = module.__getattribute__("test")
            test()

    def start(self):
        j.servers.threebot.local_start_default(background=True)

        try:
            j.servers.myjobs.schedule(self._start_libs(), die=False)
        except Exception as e:
            raise j.exceptions.RuntimeError("problem in my jobs %s", str(e))
        try:
            j.servers.myjobs.schedule(self._start_core(), die=False)
        except Exception as e:
            raise j.exceptions.RuntimeError("problem in my jobs %s", str(e))
        try:
            j.servers.myjobs.schedule(self._start_threebot(), die=False)
        except:
            raise j.exceptions.RuntimeError("problem in my jobs %s", str(e))

        print("ALL TEST OK")

    def _start_libs(self):
        for test in dir(j.tools.tester):
            if test.startswith("test_libs_"):
                test_start = self.__getattribute__(test)
                test_start()

    def _start_core(self):
        jobs_objs = []
        for test in dir(j.tools.tester):
            if test.startswith("test_core_"):
                test_start = self.__getattribute__(test)
                test_start()

    def _start_threebot(self):
        for test in dir(j.tools.tester):
            if test.startswith("test_threebot_"):
                test_start = self.__getattribute__(test)
                test_start()
