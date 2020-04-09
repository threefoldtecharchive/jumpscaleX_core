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
            "j.data.capnp.test()",
            # "j.data.nacl.test()",
            "j.data.schema.test()",
            "j.data.types.test()",
            "j.clients.sshkey.test()",
            "j.clients.sshagent.test()",
            "j.clients.ssh.test()",
            "j.sal.bcdbfs.test()",
            "j.tools.threebot.packages.test()",
            "j.tools.syncer.test()",
            "j.tools.executor.test()",
            "j.tools.time.test()",
            "j.tools.formatters.test()",
            "j.tools.threegit.test()",
            "j.tools.logger.test()",
            "j.tools.jinja2.test()",
            "j.tools.restic.test()",
            "j.clients.redis.test()",
            "j.clients.tfgrid_registry.test()",
            "j.clients.sqlitedb.test()",
            "j.clients.currencylayer.test()",
            "j.clients.sonic.test()",
            "j.clients.rdb.test()",
            "j.clients.redis_config.test()",
            "j.clients.threebot.test()",
            "j.clients.tcp_router.test()",
            "j.clients.zdb.test()",
            "j.servers.gedis.test()",
            "j.servers.threebot.test()",
            "j.servers.openresty.test()",
            "j.servers.myjobs.test()",
            "j.servers.sonic.test()",
            "j.servers.corex.test()",
            "j.servers.tmux.test()",
            "j.servers.zdb.test()",
        ]
    )
    def test(self, cmd):
        if cmd == "j.clients.zdb.test()":
            self.skipTest("This test shouldn't be run on CI, as it depends on machine speed (performance test)")
        else:
            eval(cmd)
