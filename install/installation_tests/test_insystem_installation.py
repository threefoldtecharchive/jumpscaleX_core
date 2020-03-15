import os
import platform
import subprocess
import uuid
from loguru import logger


def info(message):
    logger.info(message)


def os_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = process.communicate()
    return output, error


def get_os_type():
    os = platform.system()
    if os == "Darwin":
        return "Mac"
    return os


def rand_str(size=10):
    return str(uuid.uuid4()).replace("-", "")[:size]


def after():
    info("Clean the installation")
    command = "rm -rf /sandbox/ ~/sandbox/ /tmp/jsx /tmp/jumpscale/ /tmp/InstallTools.py"
    os_command(command)


def jumpscale_installation(install_type, options=" "):
    info("copy installation script to /tmp")
    command = "curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/master/install/jsx.py?$RANDOM > /tmp/jsx"
    os_command(command)

    info("Change installer script [/tmp/jsx] to be executed ")
    command = "chmod +x /tmp/jsx"
    os_command(command)
    info("Configure the no-interactive option")
    command = "/tmp/jsx configure -s --secret mysecret"
    os_command(command)

    info("Run script with {} with branch master".format(install_type))
    command = "/tmp/jsx {} -s {}".format(install_type, options)
    output, error = os_command(command)
    return output, error


def Test01_install_jumpscale_insystem_no_interactive():
    """
    test TC58
    ** Test installation of Jumpscale using insystem non-interactive option on Linux or mac OS **
    #. Install jumpscale from specific branch
    #. Run kosmos ,should succeedthreebotbuilder
    """
    info("Install jumpscale on {}".format(get_os_type))
    output, error = jumpscale_installation("install")
    assert error is False
    assert "installed successfully" in output.decode()

    info("Run kosmos shell,should succeed")
    command = ". /sandbox/env.sh && kosmos 'from Jumpscale import j; print(j)'"
    output, error = os_command(command)
    assert error is False
    assert "Jumpscale.Jumpscale object" in output.decode()


def Test02_verify_generate():
    """
    test TC59
    **  test jumpscale inssystem on mac or linux depending on os_type. **
    #. Run jsx generate command, should run successfully, and generate.
    """
    info("Install jumpscale on {}".format(os_type))
    output, error = jumpscale_installation("install")
    assert error is False
    assert "installed successfully" in output.decode()

    info("Check generate option, using jsx generate cmd")

    info("remove jumpscale_generated file")
    os.remove("/sandbox/lib/jumpscale/jumpscale_generated.py")

    info("Check generate option")
    command = ". /sandbox/env.sh && /tmp/jsx generate"
    output, error = os_command(command)
    assert "process" in output.decode()

    info("make sure that jumpscale_generated file is generated again")
    assert os.path.exists("/sandbox/lib/jumpscale/jumpscale_generated.py")


def Test03_insystem_installation_r_option_no_jsx_before():
    """
    test TC73, TC85
    ** Test installation of Jumpscale using insystem non-interactive and re_install option on Linux or mac OS **
    ** with no JSX installed before **
    #. Install jumpscale from specific branch
    #. Run kosmos ,should succeed
    """

    info("Install jumpscale on {} using no_interactive and re-install".format(os_type))
    output, error = jumpscale_installation("install", "-r")
    assert error is False
    assert "installed successfully" in output.decode()

    info(" Run kosmos shell,should succeed")
    command = ". /sandbox/env.sh && kosmos 'from Jumpscale import j; print(j)'"
    output, error = os_command(command)
    assert error is False
    assert "Jumpscale.Jumpscale object" in output.decode()


def Test04_insystem_installation_r_option_jsx_installed_before():
    """
    test TC74, TC86
    ** Test installation of Jumpscale using insystem non-interactive and re_install option on Linux or mac OS **
    ** with JSX installed before **
    #. Install jumpscale from specific branch
    #. Run kosmos ,should succeed
    """

    info("Install jumpscale on {}".format(get_os_type))
    output, error = jumpscale_installation("install")
    assert error is False
    assert "installed successfully" in output.decode()

    info("Install jumpscale on {} using no_interactive and re-install".format(get_os_type))

    output, error = jumpscale_installation("install", "-r")
    assert error is False
    assert "installed successfully" in output.decode()

    info(" Run kosmos shell,should succeed")
    command = ". /sandbox/env.sh && kosmos 'from Jumpscale import j; print(j)'"
    output, error = os_command(command)
    assert error is False
    assert "Jumpscale.Jumpscale object" in output.decode()


def Test06_check_option():
    """
    test TC205, TC206
    ** test check option on Linux and Mac OS **
    #. test that check option is working correctly.
    #. check option ,ake sure that secret, private key, bcdband kosmos are working fine.
    """

    info("Install jumpscale on {}".format(os_type))
    output, error = jumpscale_installation("install")
    assert error is False
    assert "installed successfully" in output.decode()

    info("test jsx check option ")
    command = ". /sandbox/env.sh && jsx check"
    output, error = os_command(command)
    assert error is False


def Test07_package_new():
    """
    ** test package-new  option **
    #. test that package-new option is working correctly.
    """

    info("Install jumpscale on {}".format(get_os_type))
    output, error = jumpscale_installation("install")
    assert error is False
    assert "installed successfully" in output.decode()

    info("Use package-new option ")
    package_name = rand_str()
    destionation = "/tmp/"
    command = f"bash -c 'source /sandbox/env.sh; /tmp/jsx  package-new --name {package_name} --dest {destionation}'"
    output, error = os_command(command)

    info("check that package added successfully.")
    command = "ls {}/{}".format(destionation, package_name)
    output, error = os_command(command)
    assert "actors" in output.decode()
    assert "chatflows" in output.decode()
    assert "models" in output.decode()
    assert "wiki" in output.decode()

    command = "ls {}/{}/actors".format(destionation, package_name)
    output, error = os_command(command)
    assert f"{package_name}.py" in output.decode()
