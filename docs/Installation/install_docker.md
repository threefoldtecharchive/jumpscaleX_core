
# install using docker (recommended)

## get the jsx tool

- see [README.md]

## if needed reset your environment

```bash
/tmp/jsx containers-reset
```


**PLEASE DO NOT USE MANUAL DOCKER COMMANDS, USE THE JSX TOOL AS MUCH AS POSSIBLE**

- make sure docker installed
- only tested on Ubuntu & OSX

```bash
#silent install & delete
/tmp/jsx container-install -s -d
#silent install don't delete
/tmp/jsx container-install -s
```
will install in docker, delete if exists and starting from already created docker image (is faster)

The container image has a volume to the code on your local machine inside /sandbox/code. 
If you edit the code you can then test it inside the container. So no need to edit anthing inside the container, can use your std IDE to edit code.


## to use

```bash
#to get container kosmos shell (JSX)
/tmp/jsx container-kosmos
#to get shell of the ubuntu base os underneath in the container
/tmp/jsx container-shell
``` 

## to install multiple containers

following will install 2 additional containers t1 & t2

```bash
/tmp/jsx container-install -s -d -n t1
/tmp/jsx container-install -s -d -n t2
```

to show the containers

```
/tmp/jsx container-list

 - t2         : threefoldtech/3bot             (sshport:9020)
 - t1         : threefoldtech/3bot             (sshport:9010)
 - 3bot       : threefoldtech/3bot             (sshport:9000)

```

## to access the container 

using jsx

```
jsx container-shell -n t2
```

over ssh manually
```
ssh -A root@localhost -p 9020
#handy for rsync over ssh or other tricks
```

the containers typically have ipaddresses in  172.17.0.0/16 and can reach each other

## how to build your own base images

```bash
jsx basebuilder
jsx threebotbuilder
 ```
 
 this will result in threefoldtech/base & threefoldtech/3bot on your system, you can use other names but if this name then will be used by the container installer as base which will win a lot of time.
