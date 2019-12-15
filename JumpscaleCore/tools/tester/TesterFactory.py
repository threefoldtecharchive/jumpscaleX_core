from Jumpscale import j

import os
from unittest import TestCase, skip

from parameterized import parameterized

locations = []
location_search = "__jslocation_"
for root, dirs, files in os.walk(j.core.tools.text_replace("{DIR_BASE}/code/github/threefoldtech")):
    for file in files:
        if file.endswith("Factory.py"):
            file_path = os.path.join(root, file)
            with open(file_path, "r") as f:
                content = f.read()
            if location_search in content:
                jslocation = content.find(location_search)
                location = content[content.find("=", jslocation) + 1 : content.find("\n", jslocation)]
                locations.append(location.strip().strip("'").strip('"'))


class TesterFactory(j.baseclasses.factory_testtools):
    __jslocation__ = "j.tools.tester"

    @parameterized.expand(locations)
    def start(self, location):
        module = eval(location)
        if "test" in dir(module):
            if "install" in dir(module):
                install = module.__getattribute__("install")
                install()
            test = module.__getattribute__("test")
            test()
        else:
            self.skipTest(f"{location} doesn't have test")

        print("TEST OK ALL PASSED")

