# TCPRouter Client

This client can make the connection to the tcprouter server

- Binary file is located at: `/sandbox/bin/trc`

## Usage

- get a client with a proper addresses and secret

```python
cl = j.clients.tcp_router.get("waleed", local_address="0.0.0.0:18000",remote_address="127.0.0.1:6379", secret="test")
```

- to connect

```python
cl.connect()
```

- to stop connection

```python
cl.stop()
```
