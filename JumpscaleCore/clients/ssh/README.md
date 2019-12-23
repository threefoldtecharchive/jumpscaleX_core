# SSH Client

## Example usage

- Get an sshclient

```python
ssh = j.clients.ssh.get("test_sshclient", addr="YOUR_REMOTE_MACHINE_IP")
```

- Execute command

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

- Upload file

```python
sshcl.upload("/sandbox/test_file", dest="/test_file")
```

- Download file

```python
sshcl.download("/sandbox/test_file", dest="/test_file")
```
