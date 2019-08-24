# Syncing host to remote machines

## Prepare your SSH

### Create SSHKEY key (only if you don't have one yet)

```python
j.clients.sshkey.get(name="main",
                    path=path_to_ssh_key
                    passphrase=passphrase_to_ssh_key)
```

where

- *path* : path to the ssh key
- *passphrase_to_ssh_key* : (optional) passphrase to ssh key

*NOTE*: The public key created needs to be added to the authorized hosts of the remote machine
    
### Create SSH client (opens ssh connection to remote machine)

```python
#if you only have 1 ssh key & default ssh port
cl = j.clients.ssh.get(name="remote1",addr="188.166.116.127") 
#if you have more than 1 ssh key specify
cl = j.clients.ssh.get(name="remote1",addr="188.166.116.127",port="22",sshkey_name="main") 
cl.execute("ls / ") #will execute a command remotely
cl.shell() #will open an ssh shell

```
where
- *addr* : remote machine address
- *port* : remote machine port
- *sshkey_name* : name of sshkey client created

To make sure the host and remote are connected:
```python
cl.isconnected
```
if *True* then the ssh connection is alive, otherwise *False*

If sshkey and client are already created. The instance can be set or updated in *kosmos* using the following:

#### use the kosmos features to do the same:

```python
j.clients.sshkey.default #will try to get the default SSHKEY on your machine
j.clients.ssh.remote1.addr = "188.166.116.127"
j.clients.ssh.remote1.port = 22
j.clients.ssh.remote1.sshkey_name = "main"
```

## (Sync host to remote)

### Shortest way, if ssh client was already created

```python
j.clients.ssh.remote1.syncer.sync()
```

by default will sync the digitalme & jumpscale code dirs

### more lengthy

```

syncer = j.tools.syncer.get(name="main",sshclient_name="main")  
#optional ,paths=paths_list
syncer.sync()

```
where
- *paths_list* : list of paths to be synced
    Different paths can be given for the host and source.

    - Same paths for source and destination:
        ```
        paths_list = ["path1_in_source","path2_in_source"...]
        ```
    - Different paths for source and destination:
        ```
        paths_list = ["path1_in_source:path1_in_dest","path2_in_source:path2_in_dest"...]
        ```
- *sshclient_name* : name of ssh client created

2) **Sync host to remote directories**  (continously monitor and sync when changes occur on host directory)
    ```
    syncer.sync()
    ```

