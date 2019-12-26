# TCPRouter Client

This client can make the connection to the tcprouter server

- Binary file is located at: `/sandbox/bin/trc`

## Usage

- Get a client with the proper local address, remote address and secret

```python
cl = j.clients.tcp_router.get("test_instance", local_ip="0.0.0.0", local_port=80, remote_url="myserver.local", remote_port=6379, secret="test")
```

- To connect to tcprouter backend

```python
cl.connect()
```

- To stop connection

```python
cl.stop()
```
