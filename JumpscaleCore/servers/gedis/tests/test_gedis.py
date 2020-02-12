import subprocess, uuid, random
from Jumpscale import j
from loguru import logger


skip = j.baseclasses.testtools._skip


ACTORS_PATH = j.core.tools.text_replace(
    "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/servers/gedis/pytests/test_package/actors"
)
ACTOR_FILE_1 = "simple"
ACTOR_FILE_2 = "actor"

START_SCRIPT = """
server=j.servers.gedis.get(name="{name}")
server.actor_add(path={actor_path}/{actor_file}.py, namespace="{ns}")
server.start()
"""

gedis_server = ""
namespace = ""
instance_name = ""
port = ""


def info(message):
    logger.info(message)


def rand_string(size=10):
    return str(uuid.uuid4()).replace("-", "")[1:10]


def os_command(command):
    info("Execute : {} ".format(command))
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = process.communicate()
    return output, error


def before():
    info("​Get gedis server instance.")
    global instance_name
    instance_name = rand_string()
    global port
    port = random.randint(1000, 2000)
    global gedis_server
    gedis_server = j.servers.gedis.get(name=instance_name, port=port, host="0.0.0.0")

    info("Add new actor,Start server ")
    global namespace
    namespace = rand_string()
    sc = START_SCRIPT.format(name=instance_name, actor_path=ACTORS_PATH, actor_file=ACTOR_FILE_1, ns=namespace)
    cmd = "kosmos -p '{}'".format(sc)
    j.servers.tmux.execute(cmd)


def after():
    gedis_server.stop()
    output, error = os_command("netstat -nltp | grep '{}' ".format(port))
    gedis_server.delete()
    if output.decode():
        raise AssertionError("Gedis port should be killed")


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/502")
def test01_actor_add():
    """
    - ​Get gedis server instance.
    - Add new actor,Start server.
    - Check that actor added successfully.
    """
    info("Check that actor added successfully.")
    assert namespace in gedis_server.actors_list(namespace)


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/502")
def test02_gedis_client():
    """
     - ​Get gedis server instance.
    - Add  actor ,Start server.
    - Get actor client with right namespace, should succeed.
    - check that actor loaded and client work successfully.
    - Get actor client with wrong namesapce should raise error.
    - gedis_client ping method, should return True.
    - Test gedis_client reload method with correct namespace, should pass.
    - Test gedis_client reload method with wrong namespcase.
    """
    cl = gedis_server.client_get(namespace=namespace)
    result = getattr(cl.actors, ACTOR_FILE_1).ping()
    assert result.decode() == "PONG"

    # info("Get actor client with wrong namesapce should raise error") ==> need to fix this part
    # with assertRaises(Exception):
    #     wrong_namespace = rand_string()
    #     cl = gedis_server.client_get(namespace=wrong_namespace)

    info("gedis_client ping method, should return True")
    assert cl.ping()

    info("Test gedis_client reload method with correct namespace, should pass")
    cl.reload(namespace=ACTOR_FILE_1)
    result = getattr(cl.actors, ACTOR_FILE_1).ping()
    assert result.decode() == "PONG"

    # info("Test gedis_client reload method with wrong namespcase") ==> need to fix this part
    # with assertRaises(Exception):
    #     cl.reload(namespace="WRONG_NAMESPACE")


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/502")
def test03_gedis_add_actors():
    """
    - ​Get gedis server instance.
    - Use add_actors method.
    - check that actors added and client can get from both of them .
    """
    gedis_server.stop()
    sc = """
        server=j.servers.gedis.get(name={name})
        server.actors_add(path={actor_path},namespace={ns})
        server.start()
        """.format(
        name=instance_name, actor_path=ACTORS_PATH, ns=namespace
    )
    cmd = "kosmos -p '{}'".format(sc)
    j.servers.tmux.execute(cmd)

    assert ACTOR_FILE_2 in gedis_server.actors_list(namespace)
    cl = gedis_server.client_get(namespace=namespace)
    arg_1 = random.randint(11, 55)
    arg_2 = random.randint(66, 99)
    result = getattr(cl.actors, ACTOR_FILE_2).args_in(arg_1, arg_2)
    assert "{} {} ".format(arg_1, arg_2) == result.decode()


@skip("https://github.com/threefoldtech/jumpscaleX_core/issues/502")
def test04_gedis_load_actors():
    """
    - ​Add actor to actors_data
    - Use load_actors.
    - check that actor loaded successfully.
    """
    gedis_server.stop()

    sc = """
        server=j.servers.gedis.get(name={name})
        server.actors_data = "{ns}:{actor_path}/{actor_file}.py".format(namespace, ACTORS_PATH, ACTOR_FILE_2)
        server.load_actors()
        server.start()
        """.format(
        name=instance_name, actor_path=ACTORS_PATH, ns=namespace, actor_file=ACTOR_FILE_2
    )
    cmd = "kosmos -p '{}'".format(sc)
    j.servers.tmux.execute(cmd)

    assert ACTOR_FILE_2 == gedis_server.actors_list(namespace)
    cl = gedis_server.client_get(namespace=namespace)
    arg_1 = random.randint(11, 55)
    arg_2 = random.randint(66, 99)
    result = getattr(cl.actors, ACTOR_FILE_2).args_in(arg_1, arg_2)
    assert "{} {} ".format(arg_1, arg_2) == result.decode()
