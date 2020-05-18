"""manage container images"""

from .lib.SDKContainers import SDKContainers
from .core import core
from .args import args
import os

IT = core.IT

_containers = SDKContainers(core=core, args=args)

__all__ = ["base_build", "phusion_build", "sdk", "sdktool", "container_import", "container_export"]


def phusion_build(push: bool = False):
    """
    build the ubuntu base container
    """
    path = IT.Tools.text_replace("{DIR_BASE}/code/github/threefoldtech/baseimage-docker")
    if not os.path.exists(path):
        IT.Tools.code_github_get(url="https://github.com/threefoldtech/baseimage-docker", branch="master")
    cmd = """
            set -ex
            cd {}/image
            docker build . -t threefoldtech/phusion:latest
        """.format(
        path
    )
    IT.Tools.execute(cmd, interactive=True)
    if push:
        IT.Tools.execute("docker pushe threefoldtech/phusion/latest")


def base_build(dest=None, push: bool = False, delete: bool = True):
    """
    build the base container
    """
    print("build phusion")
    phusion_build(push=push)
    print("build phusion done")
    if not dest:
        dest = "threefoldtech/base2"

    # image = "threefoldtech/phusion:19.10"
    image = "threefoldtech/phusion:latest"
    print("get container with phusion image")
    docker = IT.DockerFactory.container_get(name="base2", delete=delete, image=image)
    print("install container")
    docker.install(update=True, stop=delete)
    cmd = "apt install python3-brotli python3-blosc cython3 cmake -y"
    docker.dexec(cmd)
    docker.save(image=dest, clean=True)
    if push:
        docker.push()
        if delete:
            docker.stop()
    print("- *OK* base has been built, as image & exported")


def sdktool():
    """
    build the sdk tool as a binary and will copy to /tmp directory
    """
    # TODO: call the local jumpscale installer

    DIR_BASE = IT.MyEnv.config["DIR_BASE"]
    DIR_HOME = IT.MyEnv.config["DIR_HOME"]
    if IT.MyEnv.platform_is_osx:
        name = "osx"
    elif IT.MyEnv.platform_is_linux:
        name = "linux"
    else:
        raise IT.Tools.exceptions.Input("platform not supported")

    C = f"""
    cd {DIR_BASE}/installer
    rm -rf dist
    rm -rf build
    bash package.sh
    cp {DIR_BASE}/installer/dist/3sdk /tmp/3sdk_{name}
    """
    IT.Tools.execute(C)
    if IT.MyEnv.platform_is_osx:
        IT.Tools.execute(f"cp {DIR_BASE}/installer/dist/3sdk {DIR_HOME}/Downloads/3sdk_{name}", die=False)
    C = f"""
    cd {DIR_BASE}/installer
    rm -rf dist
    rm -rf build
    echo "find the build sdk on /tmp/3sdk_{name} or ~/Downloads/3sdk_{name}"
    """
    IT.Tools.execute(C)


def container_import(name=None, path=None, imagename="threefoldtech/3bot2", no_start: bool = False):
    """
    import container from image file, if not specified will be /tmp/3bot2.tar
    :param args:
    :return:
    """
    docker = _containers.get(delete=True, name=name)
    docker.import_(path=path, image=imagename)
    if not no_start:
        docker.start()


def container_export(name=None, path=None, version=None):
    """
    export the 3bot to image file, if not specified will be /tmp/3bot2.tar
    :param name:
    :param path:
    :return:
    """
    docker = _containers.get(delete=True, name=name)
    docker.export(path=path, version=version)


def sdk(push: bool = False, base: bool = False, delete: bool = False, noclean: bool = False, development: bool = False):
    """
    build the sdk (threebot) container
    """
    if base:
        base_build(push=push)
    dest = "threefoldtech/3bot2"

    docker = IT.DockerFactory.container_get(name="3botdev", delete=delete, image="threefoldtech/base2")

    docker.install(update=delete, stop=delete)

    # we know its a ubuntu 19.10 so we can install

    installer = IT.JumpscaleInstaller()
    installer.repos_get(pull=False)

    docker.install_jumpscale(force=delete, pull=False, threebot=True)
    # because identity==build the secret will be build
    # the hex/hashed repr of the secret: 'b0da275520918e23dd615e2a747528f1'

    docker._install_tcprouter()
    docker.install_jupyter()
    docker.execute("apt-get install restic -y")

    docker.image = dest

    if noclean:
        docker.save(image=dest)
        docker.delete()
    else:
        docker.save(development=development, image=dest, code_copy=True, clean=True)

    print(" - *OK* threebot container has been built, as image")

    if push:
        docker.push()
        print(" - *OK* threebot image has been exported")
