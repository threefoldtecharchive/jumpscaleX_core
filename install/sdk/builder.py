from .core import core

IT = core.IT


def base():
    """
    build the ubuntu base container
    """
    # TODO: ubuntu base
    raise RuntimeError("implement")


def sdk():
    """
    build the sdk (threebot) container
    """
    # TODO: threebot container build, see code below
    raise RuntimeError("implement")


def sdktool():
    """
    build the sdk tool as a binary and will copy to /tmp directory
    """
    # TODO: call the local jumpscale installer

    DIR_BASE = IT.MyEnv.config["DIR_BASE"]
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
    rm -rf dist
    rm -rf build
    echo "find the build sdk on /tmp/3sdk_{name}"
    """
    IT.Tools.execute(C)


def container_import(name=None, path=None, imagename="threefoldtech/3bot2", no_start=False):
    """
    import container from image file, if not specified will be /tmp/3bot2.tar
    :param args:
    :return:
    """
    # TODO: implement container_import
    raise RuntimeError("implement")
    docker = container_get(delete=True, name=name)
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
    # TODO: implement container_export
    raise RuntimeError("implement")

    docker = container_get(name=name)
    docker.export(path=path, version=version)


# def builder(push=False, base=False, delete=False, noclean=False, development=False):
#     """
#     create the 3bot and 3botdev images
#     """
#     if base:
#         basebuilder_(push=push)
#     dest = "threefoldtech/3bot2"
#
#     docker = e.DF.container_get(name="3botdev", delete=delete, image="threefoldtech/base2")
#
#     docker.install(update=delete, stop=delete)
#
#     # we know its a ubuntu 19.10 so we can install
#
#     installer = IT.JumpscaleInstaller()
#     installer.repos_get(pull=False)
#
#     docker.install_jumpscale(force=delete, pull=False, threebot=True, identity="build", reset=True)
#     # because identity==build the secret will be build
#     # the hex/hashed repr of the secret: 'b0da275520918e23dd615e2a747528f1'
#
#     docker._install_tcprouter()
#     docker.install_jupyter()
#     # docker.execute("rm  /sandbox/bin/micro;cd /tmp;curl https://getmic.ro | bash;mv micro /sandbox/bin")
#     docker.execute("apt install restic -y")
#     docker._install_package_dependencies()
#
#     docker.image = dest
#
#     if noclean:
#         docker.save(image=dest)
#         docker.delete()
#     else:
#         docker.save(development=development, image=dest, code_copy=True, clean=True)
#
#     if push:
#         docker.push()
#
#     print(" - *OK* threebot container has been built, as image & exported")
#     print(" - if you want to test the container do 'jsx container-shell -d'")
#     print(" - if you want to push you can do 'jsx container-save -p -cd' after playing with it.")
#
#
# def _build_phusion(push=False):
#     path = IT.Tools.text_replace("{DIR_BASE}/code/github/threefoldtech/baseimage-docker")
#     if not os.path.exists(path):
#         IT.Tools.code_github_get(url="https://github.com/threefoldtech/baseimage-docker", branch="master")
#     cmd = """
#         set -ex
#         cd {}/image
#         docker build . -t threefoldtech/phusion:latest
#     """.format(
#         path
#     )
#     IT.Tools.execute(cmd, interactive=True)
#     if push:
#         IT.Tools.execute("docker pushe threefoldtech/phusion/latest")
#
#
# def basebuilder_(dest=None, push=False, delete=True):
#     _build_phusion(push=push)
#     if not dest:
#         dest = "threefoldtech/base2"
#
#     # image = "threefoldtech/phusion:19.10"
#     image = "threefoldtech/phusion:latest"
#     docker = e.DF.container_get(name="base2", delete=delete, image=image)
#     docker.install(update=True, stop=delete)
#     cmd = "apt install python3-brotli python3-blosc cython3 cmake -y"
#     docker.dexec(cmd)
#     docker.save(image=dest, clean=True)
#     if push:
#         docker.push()
#         if delete:
#             docker.stop()
#     print("- *OK* base has been built, as image & exported")
