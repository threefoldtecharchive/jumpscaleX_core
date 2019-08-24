## Jumpscale Executors

Jumpscale comes with its own executors that abstract working locally or remotely.

### Local Executor

The local executor is used for executing all kinds of commands locally.
To use a local executor on a `jumpscale` shell

```python3
local_executor = j.tools.executor.local_get()
local_executor.execute('pwd')
local_executor.file_write('/tmp/foo', 'hello world')

local_executor.file_read('/tmp/foo')
```

### SSH Executor

This executor is very useful for remote execution. It takes an _SSH Client_ as an argument

#### SSH Client

Jumpscale supports two modes for the ssh client. `paramiko` and `parallel-ssh with ssh2`

to use the sshclient, you'll first have to create an **sshkey** instance. For example:

```python
# To use paramiko, just set the use_paramiko argument to True

ssh_key =  j.clients.sshkey.get(instance='example_key', data=dict(path='/root/.ssh/id_rsa'))
ssh_client = j.clients.ssh.get(instance="example_client", data=dict(addr="10.0.3.9", login="root", sshkey='example_key', allow_agent=True), use_paramiko=False)
```

After this you have created an `ssh_client` instance that you can use in your executor. For example:

```python
remote_executor = j.tools.executor.ssh_get(ssh_client)
remote_executor.execute('pwd')
remote_executor.file_write('/tmp/foo', 'hello world')

remote_executor.file_read('/tmp/foo')
```

### Docker Executor

This executor deals with local dockers. Using `docker execute`, it doesn't require the docker having ssh running

To use a docker executor:

```python
# init with container id or name
docker_executor = j.tools.executor.getLocalDocker('example')
docker_executor.execute('pwd')
docker_executor.file_write('/tmp/foo', 'hello world')

docker_executor.file_read('/tmp/foo')
```
