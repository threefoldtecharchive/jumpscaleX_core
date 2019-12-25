# SSH Client

## Example usage

- Get an sshclient

```python
ssh = j.clients.ssh.get("test_sshclient", addr="YOUR_REMOTE_MACHINE_IP")
```

### Execute command

It also replaces the known dirs by default so you can use it

```python
sshcl.execute("echo hello")
```

```python
JSX> sshcl.execute("echo hello {DIR_VAR}")
hello /sandbox/var
Connection to 69.55.49.129 closed.
(0, '', '')
```

- Complex executions
```python
# install jumpscale on a remote machine
cmd = 'export DEBIAN_FRONTEND=noninteractive;curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/development/install/jsx.py?$RANDOM > /tmp/jsx;chmod +x /tmp/jsx;rm -rf ~/.ssh/id_rsa ~/.ssh/id_rsa.pub;ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa -q -P "";/tmp/jsx install -s;'
sshcl.execute(cmd)
```

**Other parameters**

- param cmd: cmd to execute, can be multiline or even a script
- param interactive: run in a way we can interact with the execution
- param replace: replace the {} statements in the cmd (script)
- param die: die if error found
- param timeout: timeout for execution in seconds


### Upload file

```python
sshcl.upload("/sandbox/test_file", dest="/test_file")
```

**other parameters**
- param source: source file in local machine
- param dest: remote file destination
- param recursive: copy all files content recursivly
- param createdir: create the remote dir if not existed
- param ignoredir: the following are always in, no need to specify ['.egg-info', '.dist-info', '__pycache
__']
- param ignorefiles: the following are always in, no need to specify: ["*.egg-info","*.pyc","*.bak"]

### Download file

```python
sshcl.download("/sandbox/test_file", dest="/test_file")
```

**other parameters**
- param source: remote file location
- param dest: file in local machine destination
- param recursive: copy all files content recursivly
- param createdir: create the remote dir if not existed
- param ignoredir: the following are always in, no need to specify ['.egg-info', '.dist-info', '__pycache
__']
- param ignorefiles: the following are always in, no need to specify: ["*.egg-info","*.pyc","*.bak"]

### Port forwarding from remote to local

use case: you have a remote server and want to access it through local port

Example: I have nginx running on the remote machine on port 80 and I need to access it from my local 9999 port

```python
sshcl.portforward_to_local(80, 9999)
```

make sure via `curl 127.0.0.1:9999` on your local machine

### Port forwarding from local to remote

use case: the opposite of forward to local you have a local server and want to access it through remote port

```python
sshcl.portforward_to_remote(80, 9000)
```
make sure via `curl 127.0.0.1:9000` on your remote machine
