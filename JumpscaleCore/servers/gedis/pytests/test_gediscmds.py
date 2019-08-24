import os

import pytest
from DigitalMe.servers.gedis.GedisCmds import GedisCmds  # method_source_process


@pytest.mark.skip(
    reason="broken since https://github.com/threefoldtech/digitalmeX/commit/fd77fcb72150b2780d85e27db5ae4b4edd6a8539#diff-3e7b20d71613dda89b05c99227f0abb4"
)
@pytest.mark.parametrize(
    "input,code,comments,schema_in,schema_out,args",
    [
        (
            """def foo(self):
        pass""",
            "pass\n",
            "",
            "",
            "",
            [],
        ),
        (
            """def foo(self, a, b):
        pass""",
            "pass\n",
            "",
            "",
            "",
            ["a", "b"],
        ),
        (
            """def foo(self, a, b):
        \"""
        this is a comment
        \"""
        pass""",
            "pass\n",
            "this is a comment\n",
            "",
            "",
            ["a", "b"],
        ),
        (
            """def foo(self, a, b):
        \"""
        this is a comment
        ```in
        a = (O) !jumpscale.example.wallet
        ```
        ```out
        b = (O) !jumpscale.example.wallet
        ```
        \"""
        pass""",
            "pass\n",
            "this is a comment\n",
            "a = (O) !jumpscale.example.wallet\n",
            "b = (O) !jumpscale.example.wallet\n",
            ["a", "b"],
        ),
    ],
)
def test_method_source_process(input, code, comments, schema_in, schema_out, args):
    assert (code, comments, schema_in, schema_out, args) == method_source_process(input)


def test_GedisCmds_init():
    path = os.path.join(os.path.dirname(__file__), "actors/simple.py")
    cmds = GedisCmds(server=FakeServer(), namespace="default", name="test", path=path, data=None)
    assert cmds.name == "test"
    assert cmds.namespace == "default"
    assert cmds.path == path
    actual_commands = sorted(["ping", "foo", "bar", "echo"])
    assert list(cmds.cmds.keys()) == actual_commands
    for cmd in actual_commands:
        assert cmds.cmd_exists(cmd)


class FakeServer:
    def __init__(self):
        self.actors = {}
