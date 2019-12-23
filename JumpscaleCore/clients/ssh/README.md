# SSH Client

## Example usage

- Get an sshclient

```python
ssh = j.clients.ssh.get("test_sshclient", addr="69.55.49.129")
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

- Upload file

```python
sshcl.upload("/sandbox/test_file", dest="/test_file")
```

- Download file

```python
sshcl.download("/sandbox/test_file", dest="/test_file")
```
