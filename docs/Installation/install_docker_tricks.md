# tricks how to use docker for install


## all in one example using jumpscale

start the syncer to get code on remote host
```python
#ipaddress is from the remote ubuntu VM, forward your SSH key
#this will get your local jumpscale code repo's on remote machine and will keep them in sycn
r = j.clients.ssh.get(name="remote1", addr="10.18.0.7")
r.syncer.sync()
```

now start the installer remotely
```python
r = j.clients.ssh.remote1
#will install in docker a full jumpscale environment in the VM, if docker doesn't exist will install it
r.execute("python3  /sandbox/code/github/threefoldtech/jumpscaleX/install/install.py -3 --name=test -y")
```

## step by step

### prepare the VM


```
#use -A to make sure your SSH key is forwarded to the remote machine
#ipaddress is from the remote ubuntu VM, forward your SSH key
ssh -A root@ipaddress  

#INSTALL DOCKER
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
apt update
apt upgrade -y    
sudo apt install docker-ce

```


### Install Docker on ubuntu

```bash
#use -A to make sure your SSH key is forwarded to the remote machine
ssh -A root@ipaddress

apt  install docker.io -y
```

### example

make sure you got the jumpscale installer as described in [install](install.md)  (from Git or download over curl)

#### basic docker install

```bash
python3 /tmp/install.py -3 --name=test -d -y -c --secret="ssh"
```

will use secret from ssh and autogenerate the private key
will delete if container exists

#### start from an image

```
python3 /tmp/install.py -3 --portrange=3 --name=test --image=despiegk:jsx_develop -d -y -c
```

- will be unattended
  
#### continue where left off last time

```
python3 /tmp/install.py -3 --portrange=3 --name=test -y
```


### export running docker

```
docker export kds -o ~/Downloads/docker_kds.tar
```

kds is the name of the docker container can see with

### export image

```
docker image save despiegk/jsx_develop -o ~/Downloads/docker_image_despiegk_jsx_develop.tar 

```

### see which dockers running

```docker ps -a ```

### go inside docker without ssh

```docker exec -ti bf580d0240fc bash```

the id is from docker ps

### how to do installer from an existing docker image

```

```


