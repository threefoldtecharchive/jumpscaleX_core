# SSH client

## Example usage:

- Get ssh client instance

```python
ssh = j.clients.ssh.get(name="test_sshclient", addr="69.55.49.129", client_type="paramiko")
```

- Execute remote commands

```python
ssh.execute("echo hello")
```
