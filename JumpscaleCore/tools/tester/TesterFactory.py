from Jumpscale import j

from parameterized import parameterized

locations_libs = []
locations_core = []
locations_threebot = []


def _get_all_tests(locations, path):

    location_search = "__jslocation_"
    for file_path in j.sal.fs.listFilesInDir(
        path=j.core.tools.text_replace(path), filter="*Factory.py", recursive=True
    ):
        content = j.sal.fs.readFile(file_path)
        if location_search in content:
            jslocation = content.find(location_search)
            location = content[content.find("=", jslocation) + 1 : content.find("\n", jslocation)]
            if location:
                locations.append(location.strip().strip("'").strip('"'))


_get_all_tests(locations_libs, "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_libs")
_get_all_tests(locations_core, "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_core")
_get_all_tests(locations_threebot, "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_threebot")


class TesterFactory(j.baseclasses.factory_testtools):
    __jslocation__ = "j.tools.tester"

    @parameterized.expand(locations_core)
    def test_core(self, location):
        module = eval(location)
        if "test" in dir(module):
            test = getattr(module, "test")
            test()

    @parameterized.expand(locations_libs)
    def test_libs(self, location):
        module = eval(location)
        if "test" in dir(module):
            test = getattr(module, "test")
            test()

    @parameterized.expand(locations_threebot)
    def test_threebot(self, location):
        module = eval(location)
        if "test" in dir(module):
            test = getattr(module, "test")
            test()

    def start(self):
        def run_test(test_name):
            test_function = getattr(j.tools.tester, test_name)
            if test_function:
                test_function()

        jobs = []
        j.servers.threebot.local_start_default(background=True)

        for test in dir(j.tools.tester):
            if test.startswith("test_"):
                jobs.append(j.servers.myjobs.schedule(run_test, test_name=test))

        try:
            j.servers.myjobs.wait([job.id for job in jobs])
        except Exception as e:
            pass

        for job in jobs:

            if job.state == "OK":
                print("%s SUCCESS" % job.id)
            elif job.state == "NEW":
                print("%s Waiting" % job.id)
            else:
                print("Job failed", job.result)

