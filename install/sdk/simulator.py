def install():
    """
    install & run a container with SDK & simulator
    a connection to zerotier network will be made
    """
    jsx.container_stop.callback(name)


def delete():
    """
    stop simulator & remove the container
    """
    jsx.container_stop.callback(name)


def start():
    """
    start simulator in the container if it was stopped before
    """
    jsx.tfgrid_simulator.callback(name)


def stop():
    """
    stop the simulator, container remains but simulator stops
    """
    jsx.tfgrid_simulator.callback(name)


def restart():
    """
    restart the simulator, this can help to remove all running kernels
    the pyjupyter notebook can become super heavy
    """
    jsx.tfgrid_simulator.callback(name)


def shell():
    """
    get a shell into the simulator
    """
    jsx.container_shell.callback(name)


# def tfgrid_simulator(delete=False, restart=False, shell=False, browser=True, stop=False):
#     """
#     start the 3bot container
#     :param name:
#     :return:
#     """
#
#     if stop:
#         d = e.DF.container_get("simulator")
#         d.stop()
#         d.delete()
#         return
#     docker = container_get(name="simulator", delete=delete)
#
#     if restart:
#         if not docker.info["State"]["Status"] == "running":
#             docker.start()
#         else:
#             j = jumpscale_get()
#             j.servers.notebook.stop(background=True)
#             j.servers.notebook.start(background=True)
#     else:
#         docker.start()
#         addr = docker.zerotier_connect()
#         docker.execute("j.tools.tfgrid_simulator.start(background=True)", jumpscale=True)
#         print(f" - CONNECT TO YOUR SIMULATOR ON: http://{addr}:8888/")
#
#     if browser:
#         try:
#             import webbrowser
#
#             time.sleep(3)
#             if IT.MyEnv.platform_is_osx:
#                 webbrowser.get("safari").open_new_tab(f"http://{addr}:8888")
#             else:
#                 webbrowser.open_new_tab(f"http://{addr}:8888")
#         except:
#             pass
#
#     if shell:
#         docker.shell()
