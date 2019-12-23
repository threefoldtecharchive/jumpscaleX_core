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
        core_tests = Core()
        libs_tests = Libs()
        threebot_tests = Threebot()

        try:
            # Tests of core
            j.servers.myjobs.schedule(core_tests.clients)
            j.servers.myjobs.schedule(core_tests.data)
            j.servers.myjobs.schedule(core_tests.servers)
            j.servers.myjobs.schedule(core_tests.tools)
            j.servers.myjobs.schedule(core_tests.sal)
            # Tests of libs
            j.servers.myjobs.schedule(libs_tests.tests)
            # Tests of threebot
            j.servers.myjobs.schedule(threebot_tests.tests)
        except Exception as e:
            raise j.exceptions.RuntimeError("problem in my jobs %s", str(e))

        print("ALL TEST OK")


class Threebot:
    def tests():
        for test in dir(j.tools.tester):
            if test.startswith("test_threebot_"):
                test_start = j.tools.tester.__getattribute__(test)
                test_start()


class Core:
    def clients():

        core_clients = [x for x in dir(j.tools.tester) if "core_" in x and "clients" in x]
        for test in core_clients:
            test_start = j.tools.tester.__getattribute__(test)
            test_start()

    def data():
        core_data = [x for x in dir(j.tools.tester) if "core_" in x and "data" in x]
        for test in core_data:
            test_start = j.tools.tester.__getattribute__(test)
            test_start()

    def servers():
        core_servers = [x for x in dir(j.tools.tester) if "core_" in x and "servers" in x]
        for test in core_servers:
            test_start = j.tools.tester.__getattribute__(test)
            test_start()

    def tools():
        core_tools = [x for x in dir(j.tools.tester) if "core_" in x and "tools" in x]
        for test in core_tools:
            test_start = j.tools.tester.__getattribute__(test)
            test_start()

    def sal():
        core_sal = [x for x in dir(j.tools.tester) if "core_" in x and "sal" in x]
        for test in core_sal:
            test_start = j.tools.tester.__getattribute__(test)
            test_start()


class Libs:
    def tests():
        for test in dir(j.tools.tester):
            if test.startswith("test_libs_"):
                test_start = j.tools.tester.__getattribute__(test)
                test_start()
