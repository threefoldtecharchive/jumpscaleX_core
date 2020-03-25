from Jumpscale import j
import nose, os


def test_unittests():
    """
    to run:

    kosmos 'j.data.schema.test(name="unittests")' --debug
    """
    unittests_path = j.core.tools.text_replace(
        "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/data/schema/tests/testsuite"
    )
    os.chdir(unittests_path)
    nose.run(argv=["", unittests_path])
