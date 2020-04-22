from .lib.SDKContainers import SDKContainers
from .core import core
from .args import args
import os

IT = core.IT

_containers = SDKContainers(core=core, args=args)

__all__ = ["base", "sdk", "sdktool", "container_import", "container_export"]

def base(push=False):
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



def sdk(dest=None, push=False, delete=True):
    """
    build the sdk (threebot) container
    """
    print("build phusion")
    base(push=push)
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
        name = "osx"
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


def container_import(name=None, path=None, imagename="threefoldtech/3bot2", no_start=False):
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
