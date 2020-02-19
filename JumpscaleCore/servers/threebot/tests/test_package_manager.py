from uuid import uuid4

from Jumpscale import j
from parameterized import parameterized


PACKAGE_NAME = "test_package"
path = "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/examples/test_package"
result_path = j.sal.fs.joinPaths(path, "result")
gedis_client = j.clients.gedis.get("pm", port=8901, package_name="zerobot.packagemanager")
package_manager = gedis_client.actors.package_manager
skip = j.baseclasses.testtools._skip


def random_string():
    return str(uuid4())[:10]


def info(message):
    j.tools.logger._log_info(message)


def get_package(package_name):
    packages = package_manager.packages_list().packages
    for package in packages:
        if package_name in package.name:
            return package
    return None


def before_all():
    j.servers.threebot.start(background=True)


def after():
    package_manager.package_delete(PACKAGE_NAME)
    j.sal.fs.remove(result_path)


def after_all():
    j.servers.threebot.default.stop()


@parameterized.expand(["path", "giturl"])
def test_001_package_add(method):
    """
    Test case for adding package (test package) in threebot server

    **Test scenario**
    #. Start threebot server.
    #. Add test package.
    #. Check that the test package has been added.
    """
    info("Add test package.")

    if method == "path":
        package = {"path": path}
    else:
        giturl = "https://github.com/threefoldtech/jumpscaleX_threebot/tree/development_testrunner/ThreeBotPackages/examples/test_package"
        package = {"git_url": giturl}

    package_manager.package_add(**package)
    gedis_client.reload()

    info("Check that the test package has been added.")
    content = j.sal.fs.readFile(result_path)
    assert "preparing package" in content
    assert "starting packag" in content


def test_002_package_list_delete():
    """
    Test case for listing and deleting packages

    **Test scenario**
    #. Start threebot server.
    #. Add test package.
    #. List packages, test package should be found.
    #. Delete test package.
    #. List packages again, test package should not be found.
    """
    info("Add test package.")
    package_manager.package_add(path=path)
    gedis_client.reload()

    info("List packages, test_package should be found.")
    package = get_package(PACKAGE_NAME)
    assert package is not None

    info("Delete test package.")
    package_manager.package_delete(package.name)
    content = j.sal.fs.readFile(result_path)
    assert "uninstalling package" in content

    # TODO: check that there is no model in bcdb for this package

    info("List packages again, test_package should not be found.")
    package = get_package(PACKAGE_NAME)
    assert package is None


def test_003_package_enable_disable():
    """
    Test case for enabling and disabling packages.

    **Test scenario**
    #. Add test package.
    #. Disable this package.
    #. Check that package
    #. Enable this package.
    #. Check that package is enabled.

    """
    info("Add test package.")
    package_manager.package_add(path=path)
    gedis_client.reload()

    package = get_package(PACKAGE_NAME)
    assert package is not None
    assert package.status == "INSTALLED"

    info("Disable this package.")
    package_manager.package_disable(package.name)

    info("Check that package")
    package = get_package(PACKAGE_NAME)
    assert package is not None
    assert package.status == "DISABLED"

    info("Enable this package.")
    package_manager.package_enable(package.name)

    info("Check that package is enabled.")
    package = get_package(PACKAGE_NAME)
    assert package is not None
    assert package.status == "INSTALLED"


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/510")
def test_004_package_start_stop():
    """
    Test case for starting and stopping packages.

    **Test scenario**
    #. Add test package.
    #. Stop this package.
    #. Check that this package has been stopped.
    #. Start this package.
    #. Check that this package has been started.
    """
    info("Add test package.")
    package_manager.package_add(path=path)
    gedis_client.reload()

    package = get_package(PACKAGE_NAME)
    assert package is not None
    assert package.status == "INSTALLED"

    info("Stop this package.")
    package_manager.package_stop(package.name)

    info("Check that this package has been stopped.")
    package = get_package(PACKAGE_NAME)
    assert package is not None
    assert package.status == "HALTED"

    content = j.sal.fs.readFile(result_path)
    assert "stopping package" in content
    j.sal.fs.remove(result_path)

    info("Start this package.")
    package_manager.package_start(package.name)

    info("Check that this package has been started.")
    package = get_package(PACKAGE_NAME)
    assert package is not None
    assert package.status == "INSTALLED"

    content = j.sal.fs.readFile(result_path)
    assert "starting package" in content

