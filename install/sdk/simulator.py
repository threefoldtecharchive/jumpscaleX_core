def stop(name="simulator"):
    """
    Stop simulator
    """
    jsx.container_stop.callback(name)


def start(name="simulator"):
    """
    Start simulator
    """
    jsx.tfgrid_simulator.callback(name)


def shell(name="simulator"):
    """
    Shell for simulator
    """
    jsx.container_shell.callback(name)


def kosmos(name="simulator"):
    """
    Start kosmos shell on simulator
    """
    jsx.kosmos.callback(name)


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
