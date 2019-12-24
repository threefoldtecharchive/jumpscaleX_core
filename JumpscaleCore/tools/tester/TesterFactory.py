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
        for file_path in j.sal.fs.listFilesInDir(
            path=j.core.tools.text_replace(path), filter="*Factory.py", recursive=True
        ):
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
        def run_test(test_name):
            test_function = j.tools.tester.__getattribute__(test_name)
            if test_function:
                test_function()

        jobs = []
        j.servers.threebot.local_start_default(background=True)

        for test in dir(j.tools.tester):
            if not test.endswith("_") and test.startswith("test_"):
                jobs.append(j.servers.myjobs.schedule(run_test, test_name=test))

        for job in jobs:

            job.wait()

            if job.state == "OK":
                print("%s SUCCESS" % job.id)
            else:
                print("Job failed", job.result)

