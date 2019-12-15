import os
from Jumpscale import j
from parameterized import parameterized
from unittest import TestCase

locations = []
for root, dirs, files in os.walk(
    j.core.tools.text_replace("{DIR_BASE}/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore")
):
    for file in files:
        if file.endswith(".py"):
            file_path = os.path.join(root, file)
            with open(file_path, "r") as f:
                content = f.read()
            if "__jslocation__ =" in content:
                jslocation = content.find("__jslocation__")
                location = content[content.find("=", jslocation) + 1 : content.find("\n", jslocation)]
                locations.append(location.strip().strip("'").strip('"'))


class FullCoreTests(TestCase):
    @parameterized.expand(locations)
    def test(self, location):
        module = eval(location)
        if "test" in dir(module):
            test = module.__getattribute__("test")
            test()
        else:
            self.skipTest(f"{location} doesn't has test")


class CoreTests(TestCase):
    @parameterized.expand(
        [
            "j.data.bcdb.test()",
            "j.data.schema.test()",
            "j.clients.sshkey.test()",
            "j.clients.sshagent.test()",
            "j.clients.zdb.test()",
            "j.servers.openresty.test()",
            "j.servers.myjobs.test()",
        ]
    )
    def test(self, cmd):
        eval(cmd)
