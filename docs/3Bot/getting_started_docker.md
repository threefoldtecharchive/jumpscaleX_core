


## preparation

### copy jsx to a running machine

- in example will use Ubuntu
- to copy with scp from a machine with jumpscale you can do

```
scp /sandbox/bin/jsx root@192.168.8.209:/tmp/;scp /sandbox/code/github/threefoldtech/jumpscaleX_core/install/InstallTools.py  root@192.168.8.209:/tmp/
```

### login

- login to the remote machine, make sure ssh-key is forwarded
- e.g. ```ssh -A root@192.168.8.209```

### reset

make sure you have no old images or containers 

```bash
jsx containers-reset
```

this will remove all images & docker containers (BE CAREFUL).

### deploy 3bots

```bash
cd /tmp
./jsx threebot-test
#if you want the webcomponents use -w
./jsx threebot-test -w
#if you want to delete your container while installing your threebot
./jsx threebot-test -w -d
#if you want to install multiple threebots talking to each other (count=3)
./jsx threebot-test -w -d -c 3
```

### work with the 3bots

to see the containers:

![](images/containers_3bot.png)

to use one of the threebots

```bash
jsx container-shell -n 3bot2
#if you want the kosmos shell
jsx container-kosmos -n 3bot2
```

### to create your own base images

Useful to have an up to date version which will speed up your deployments

```bash
#to build the base images 'threefoldtech/base' & 'threefoldtech/3bot'
#-b means will build the base as well
jsx threebotbuilder -b
```

this will have all the required components in an ubuntu to start from
and a full 3bot environment. Now its very quick to start 3bots.



