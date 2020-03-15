import platform
import subprocess
import uuid
import random
from loguru import logger

CONTAINER_NAME = ""


def info(message):
    logger.info(message)


def os_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = process.communicate()
    return output, error


def jumpscale_installation(install_type, options=" "):
    info("copy installation script to /tmp")
    command = (
        "curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/master/install/jsx.py?$RANDOM > /tmp/jsx"
    )
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


def get_os_type():
    os = platform.system()
    if os == "Darwin":
        return "Mac"
    return os


def install_jsx_container():
    info("Install container jumpscale in {} os type".format(get_os_type()))
    output, error = jumpscale_installation("container-install", "-n {}".format(CONTAINER_NAME))
    assert "installed successfully" in output.decode()
    if error:
        raise AssertionError("Installation should be run without any error")


def docker_command(command):
    command = "docker exec -i {} /bin/bash -c '{}'".format(CONTAINER_NAME, command)
    return os_command(command)


def get_loaded_key():
    command = "ssh-add -L"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    output, error = process.communicate()
    return output.decode().strip()


def rand_str(size=10):
    return str(uuid.uuid4()).replace("-", "")[:size]


def before():
    print("\t")
    global CONTAINER_NAME
    CONTAINER_NAME = str(uuid.uuid4()).replace("-", "")[:10]


def after():
    info("Clean the installation")
    command = "rm -rf /sandbox/ ~/sandbox/ /tmp/jsx /tmp/jumpscale/ /tmp/InstallTools.py"
    os_command(command)
    info("Delete jumpscale created container.")
    command = "docker rm -f {}".format(CONTAINER_NAME)
    os_command(command)

    command = "rm -rf /sandbox; rm -rf ~/sandbox"
    os_command(command)


def Test01_verify_container_kosmos_option():
    """
    TC54

    ** Test installation of container jumpscale on linux or mac depending on os_type **

    *Test libs builers sandbox*
    #. Install jumpscale from specific branch
    #. Run container-kosmos ,should succeed
    """
    install_jsx_container()
    info("Run container_kosmos ,should succeed")
    command = " echo 'from Jumpscale import j' | /tmp/jsx container-kosmos -n {}".format(CONTAINER_NAME)
    output, error = os_command(command)
    if error:
        raise AssertionError("".format(error.decode()))
    assert "BCDB INIT DONE" in output.decode()


def Test02_verify_container_stop_start_options():
    """
    TC48,TC55
    ** test  container-stop and container-start options on mac or linux depending on os_type **

    #. Check that js container exist ,should succeed.
    #. Run container stop.
    #. Check that container stopped successfully.
    #. Run container started.
    #. Check that container started successfully

    """
    install_jsx_container()
    os_type = get_os_type()
    info(" Running on {} os type".format(os_type))

    info("Run container stop ")
    command = "/tmp/jsx container-stop -n {}".format(CONTAINER_NAME)
    os_command(command)

    info("Check that container stopped successfully")
    command = "docker ps -a -f status=running  | grep {}".format(CONTAINER_NAME)
    output, error = os_command(command)
    if output:
        raise AssertionError("".format(output.decode()))

    info("Run container started ")
    command = "/tmp/jsx container-start -n {}".format(CONTAINER_NAME)
    os_command(command)

    info("Check that container started successfully")
    command = "docker ps -a -f status=running  | grep {}".format(CONTAINER_NAME)
    output, error = os_command(command)
    assert CONTAINER_NAME in output.decode()


def Test03_verify_jsx_working_inside_docker():
    """
    TC51,TC56
    ** test jumpscale inside docker on mac or linux depending on os_type. **

    #. Run kosmos command inside docker, should start kosmos shell .
    #. Run js_init generate command inside docker, sshould run successfully.
    #. Check the branch of jumpscale code, should be same as installation branch.
    """
    install_jsx_container()
    info("Run kosmos command inside docker,should start kosmos shell")
    command = """source /sandbox/env.sh && kosmos "from Jumpscale import j;print(j)" """
    output, error = docker_command(command)
    assert "Jumpscale.Jumpscale object" in output.decode()

    info("Run js_init generate ")
    command = "source /sandbox/env.sh && js_init generate"
    output, error = docker_command(command)
    if error:
        raise AssertionError("".format(error.decode()))
    assert "process" in output.decode()

    info(" Check the branch of jumpscale code, should be same as installation branch.")
    command = "cat /sandbox/code/github/threefoldtech/jumpscaleX_core/.git/HEAD"
    output, _ = docker_command(command)
    branch = output.decode().replace("\n", "").split("/")[-1]
    assert branch == "master"

    info("check  that ssh-key loaded in docker successfully")
    command = "cat /root/.ssh/authorized_keys"
    output, error = docker_command(command)
    for key in get_loaded_key().split("\n"):
        assert key == output.decode().strip("\n")


def test04_verify_container_delete_option():
    """

    **Verify that container-delete option will delete the running container**
    """
    install_jsx_container()
    info("Delete the running jsx container using container-delete")
    command = "/tmp/jsx container-delete -n {}".format(CONTAINER_NAME)
    os_command(command)

    command = "docker ps -a | grep {}".format(CONTAINER_NAME)
    output, error = os_command(command)
    if output:
        raise AssertionError("".format(output.decode()))


def test05_verify_containers_reset_option():
    """

    **Verify that containers-reset option will delete running containers and image**
    """
    install_jsx_container()
    info("Reset the running container and image using container-reset")
    command = "/tmp/jsx containers-reset".format(CONTAINER_NAME)
    os_command(command)

    info("Check that running containers have been deleted")
    command = "docker ps -aq "
    output, error = os_command(command)
    if output:
        raise AssertionError("".format(output.decode()))

    info("Check that containers image have been deleted")
    command = "docker images -aq "
    output, error = os_command(command)
    if output:
        raise AssertionError("".format(output.decode()))


def test06_verify_containers_import_export_options():
    """

    **Verify that container-import and container-export works successfully **
    """
    install_jsx_container()
    info("Use container-export ,should export the running container.")
    command = "/tmp/jsx container-export -n {}".format(CONTAINER_NAME)
    os_command(command)

    info("Create file in existing jumpscale container")
    file_name = str(uuid.uuid4()).replace("-", "")[:10]
    command = "cd / && touch {}".format(file_name)
    docker_command(command)

    info("Use container-import, should restore the container")
    command = "/tmp/jsx container-import -n {}".format(CONTAINER_NAME)
    os_command(command)

    info("Check that container does not have the file ")
    command = "ls / "
    output, error = docker_command(command)
    assert file_name not in output.decode()


# @skip("To re-do")
# def test07_verify_container_clean_options():
#     """

#     **Verify that container-clean works successfully **
#     """
#     install_jsx_container()
#     command = 'docker ps -a | grep %s | awk "{print \$2}"' % CONTAINER_NAME
#     output, error = os_command(command)
#     container_image = output.decode()

#     info("Run container stop ")
#     command = "/tmp/jsx container-stop -n {}".format(CONTAINER_NAME)
#     os_command(command)

#     info("Run container-clean with new name")
#     new_container = str(uuid.uuid4()).replace("-", "")[:10]
#     command = "/tmp/jsx container-clean -n {}".format(new_container)
#     output, error = os_command(command)
#     assertIn("import docker", output.decode())

#     info("Check that new container created with same image")
#     command = "ls /sandbox/var/containers/{}/exports/".format(new_container)
#     output, error = os_command(command)
#     assertFalse(error)
#     assertIn("tar", output.decode())

#     command = 'docker ps -a -f status=running  | grep %s | awk "{print \$2}"' % CONTAINER_NAME
#     output, error = os_command(command)
#     new_container_image = output.decode()
#     assertEqual(container_image, new_container_image)


def test08_verify_reinstall_d_option():
    """

    **Verify that container-install -d  works successfully **
    """
    install_jsx_container()
    info("Create file in existing jumpscale container")
    file_name = str(uuid.uuid4()).replace("-", "")[:10]
    command = "cd / && touch {}".format(file_name)
    docker_command(command)

    info("Run container-install -d ")
    command = "/tmp/jsx container-install -s -n {} -d  ".format(CONTAINER_NAME)
    output, error = os_command(command)
    assert "installed successfully" in output.decode()

    info("Check that new container created with same name and created file doesn't exist")
    command = "ls / "
    output, error = docker_command(command)
    assert file_name not in output.decode()


def test09_verify_reinstall_r_option():
    """

    **Verify that container-install -r  works successfully **
    """
    install_jsx_container()
    info("Remove one of default installed packages using jumpscale  in existing jumpscale container")
    command = "pip3 uninstall prompt-toolkit -y"
    docker_command(command)

    info("Add data in bcdb by get new client.")
    client_name = str(uuid.uuid4()).replace("-", "")[:10]
    command = "source /sandbox/env.sh && kosmos 'j.clients.zos.get({})'".format(client_name)
    output, error = docker_command(command)

    info("Run container-install -r ")
    command = "/tmp/jsx container-install -s -n {} -r ".format(CONTAINER_NAME)
    output, error = os_command(command)
    assert "installed successfully" in output.decode()

    info("Check that same container exist with bcdb data and removed pacakage exist.")
    command = "source /sandbox/env.sh && kosmos 'j.data.bcdb.system.get_all()'"
    output, error = docker_command(command)
    assert (data for data in output.decode() if data.name == client_name)

    command = "pip3 list | grep -F prompt-toolkit"
    output, error = os_command(command)
    assert "prompt-toolkit" in output.decode()


def test10_verify_scratch_option():
    """

    **Verify that container-install --scratch  works successfully **
    """
    install_jsx_container()

    info("Add data in bcdb by get new client.")
    client_name = str(uuid.uuid4()).replace("-", "")[:10]
    command = "source /sandbox/env.sh && kosmos 'j.clients.zos.get({})'".format(client_name)
    output, error = docker_command(command)

    info("Use container-install --scratch with same conatiner name. ")
    command = "/tmp/jsx container-install -s -n {} --scratch ".format(CONTAINER_NAME)
    output, error = os_command(command)
    assert "installed successfully" in output.decode()

    info("Check that new contianer installed without new data .")
    command = 'source /sandbox/env.sh && kosmos "print (j.data.bcdb.system.get_all())"'
    output, error = docker_command(command)
    assert client_name not in output.decode()


def test11_verify_threebot():
    """

    **Verify that container-install --threebot  works successfully **
    """
    info("Use container-install --threebot.")
    output, error = jumpscale_installation("container-install", "-n {} --threebot ".format(CONTAINER_NAME))
    if error:
        raise AssertionError("".format(error.decode()))
    assert "installed successfully" in output.decode()

    info("Check that container installed sucessfully with threboot.")
    command = 'docker ps -a -f status=running  | grep %s | awk "{print \$2}"' % CONTAINER_NAME
    output, error = os_command(command)
    container_image = output.decode()
    assert "threefoldtech/3bot" in container_image.strip("\n")

    command = "ls /sandbox/bin"
    files_list, error = docker_command(command)
    threebot_builders = [{"sonic": "apps"}, {"zdb": "db"}, {"openresty": "web"}]
    for builder in threebot_builders:
        assert list(builder.keys())[0] in files_list.decode()
        command = 'source /sandbox/env.sh && kosmos -p "getattr(getattr(j.builders,\\"{}\\"),\\"{}\\").install()"'.format(
            list(builder.values())[0], list(builder.keys())[0]
        )
        output, error = docker_command(command)
        assert "already done" in output.decode()


def test12_verify_images():
    """

    **Verify that container-install --image  works successfully **
    """
    info("Use container-install --threebot.")
    image = "threefoldtech/3bot"
    output, error = jumpscale_installation("container-install", "-n {} --image {} ".format(CONTAINER_NAME, image))
    if error:
        raise AssertionError("".format(error.decode()))
    assert "installed successfully" in output.decode()

    info("Check that container installed sucessfully with right image.")
    command = 'docker ps -a -f status=running  | grep %s | awk "{print \$2}"' % CONTAINER_NAME
    output, error = os_command(command)
    container_image = output.decode()
    assert image in container_image.strip("\n")


def test13_verify_ports():
    """

    **Verify that container-install --ports  works successfully **
    """
    info("Use container-install --ports.")
    source_port_1 = random.randint(20, 500)
    destination_port_1 = random.randint(500, 1000)

    source_port_2 = random.randint(20, 500)
    destination_port_2 = random.randint(500, 1000)
    output, error = jumpscale_installation(
        "container-install",
        "-n {} --ports {}:{} --ports {}:{} ".format(
            CONTAINER_NAME, source_port_1, destination_port_1, source_port_2, destination_port_2
        ),
    )
    if error:
        raise AssertionError("".format(error.decode()))
    assert "installed successfully" in output.decode()

    info("Check that container installed sucessfully with right ports.")
    command = "docker port {}".format(CONTAINER_NAME)
    output, error = os_command(command)
    exported_port_1 = "{}/tcp -> 0.0.0.0:{}".format(destination_port_1, source_port_1)
    exported_port_2 = "{}/tcp -> 0.0.0.0:{}".format(destination_port_2, source_port_2)
    assert exported_port_1 in output.decode()
    assert exported_port_2 in output.decode()


def test14_verify_branch():
    """

    **Verify that container-install --branch  works successfully **
    """
    info("Use container-install --branch.")
    branch = "master"
    output, error = jumpscale_installation("container-install", "-n {} --branch {}".format(CONTAINER_NAME, branch))
    if error:
        raise AssertionError("".format(error.decode()))
    assert "installed successfully" in output.decode()

    info("Check that container installed sucessfully with right branch.")
    command = "cat /sandbox/code/github/threefoldtech/jumpscaleX_core/.git/HEAD"
    output, _ = docker_command(command)
    code_branch = output.decode().replace("\n", "").split("/")[-1]
    assert branch == code_branch


def test15_verify_containers():
    """

    **Verify that /tmp/jsx containers  works successfully **
    """
    install_jsx_container()

    info("Use /tmp/jsx containers option ")
    command = "/tmp/jsx containers"
    output, error = os_command(command)

    info("Check that container exist in containers list . ")
    assert CONTAINER_NAME == output.decode()


def test16_verify_develop():
    """

    **Verify that container-install --develop  works successfully **
    """
    info("Use container-install --develop.")
    output, error = jumpscale_installation("container-install", "-n {} --develop".format(CONTAINER_NAME))
    if error:
        raise AssertionError("".format(error.decode()))
    if error:
        raise AssertionError("".format(error.decode()))
    assert "installed successfully" in output.decode()

    info("Check that container installed sucessfully with right master image.")
    command = 'docker ps -a -f status=running  | grep %s | awk "{print \$2}"' % CONTAINER_NAME
    output, error = os_command(command)
    container_image = output.decode()
    assert "threefoldtech/3botdev" in container_image.strip("\n")


def test17_verify_container_save():
    """

    **Verify that container-save  works successfully **
    """
    info("Install js container.")
    install_jsx_container()

    info(" Run container-save.")
    committed_image_name = rand_str()
    command = "/tmp/jsx container-save  -n {} --dest {}".format(CONTAINER_NAME, committed_image_name)
    output, error = os_command(command)

    info("Check that image committed successfully.")
    command = "docker images | grep %s " % committed_image_name
    output, error = os_command(command)
    assert output


def test18_verify_threebot():
    """

    **Verify that threebot-test option  works successfully **
    """
    info(" Run threebot option .")
    command = (
        "curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/master/install/jsx.py?$RANDOM > /tmp/jsx"
    )
    os_command(command)

    info("Change installer script [/tmp/jsx] to be executed ")
    command = "chmod +x /tmp/jsx"
    os_command(command)
    info("Configure the no-interactive option")
    command = "/tmp/jsx configure -s --secret mysecret"
    os_command(command)

    command = "/tmp/jsx threebot-test"
    output, error = os_command(command)

    info("Check that container installed sucessfully with right master image.")
    CONTAINER_NAME = "3bot"
    command = "docker ps -a -f status=running  | grep {}".format(CONTAINER_NAME)
    output, error = os_command(command)
    assert output.decode()

    command = "ps -aux | grep startupcmd_zdb"
    output, error = docker_command(command)
    assert output

    command = "ps -aux | grep startupcmd_sonic"
    output, error = docker_command(command)
    assert output


def test19_verify_basebuilder():
    """

    **Verify that basebuilder option  works successfully **
    """
    command = (
        "curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/master/install/jsx.py?$RANDOM > /tmp/jsx"
    )
    os_command(command)

    info("Change installer script [/tmp/jsx] to be executed ")
    command = "chmod +x /tmp/jsx"
    os_command(command)

    info("Add sshkey ")
    os_command('ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa  <<< y')
    os_command("eval `ssh-agent -s`  &&  ssh-add")

    info("Configure the no-interactive option")
    command = "/tmp/jsx configure -s --secret mysecret"
    os_command(command)

    info(" Run basebuilder option .")
    command = "/tmp/jsx  basebuilder "
    output, error = os_command(command)

    info("Check that base container installed sucessfully with right base image.")
    CONTAINER_NAME = "base"
    command = 'docker ps -a -f status=running  | grep %s | awk "{print \$2}"' % CONTAINER_NAME
    output, error = os_command(command)
    assert output.decode()
    assert "threefoldtech/base" in output.decode()


def test20_verify_pull():
    """

    **Verify that --pull option  works successfully **
    """
    install_jsx_container()
    info("Remove created container. ")
    command = "docker rm -f {}".format(CONTAINER_NAME)
    output, error = os_command(command)

    info("Checkout jumpscalex_core repo to old commit")
    command = "cd /sandbox/code/github/threefoldtech/jumpscaleX_core && git log -2"
    output, error = os_command(command)
    commits = output.decode().splitlines()
    latest_commit = commits[0][commits[0].find("commit") + 7 :]
    old_commit = commits[1][commits[1].find("commit") + 7 :]
    command = "cd /sandbox/code/github/threefoldtech/jumpscaleX_core && git checkout {}".format(old_commit)
    output, error = os_command(command)

    info("install jumpscale with container-install --pull ")
    output, error = jumpscale_installation("container-install", "-n {} --pull".format(CONTAINER_NAME))
    if error:
        raise AssertionError("".format(error.decode()))
    assert "installed successfully" in output.decode()

    info("Check that jumpscalex_core repo updated.")
    command = "cd /sandbox/code/github/threefoldtech/jumpscaleX_core && git log -1"
    output, error = os_command(command)
    assert latest_commit in output.decode()
    output, error = docker_command(command)
    assert latest_commit in output.decode()


def test21_verify_configure():
    """

    **Verify that configure options  works successfully **
    """
    install_jsx_container()
    info("Remove created container. ")
    command = "docker rm -f {}".format(CONTAINER_NAME)
    output, error = os_command(command)

    info("Use configure to update code directory. ")
    dire_name = "/root/test"
    command = "/tmp/jsx configure --codedir {}".format(dire_name)
    os_command(command)
    command = "/tmp/jsx container-install -s"

    info("Check that the directory has the code now.")
    command = "ls {}/github/threefoldtech".format(dire_name)
    output, error = os_command(command)
    assert "jumpscaleX_core" in output.decode()
