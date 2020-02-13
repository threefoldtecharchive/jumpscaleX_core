# Install JumpscaleX with Wikis and test macros

## Step 1

### Install jumpscaleX in a container with threebot using the following steps

```bash
curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/development/install/jsx.py > /tmp/jsx;
chmod +x /tmp/jsx;
/tmp/jsx container-install -s --threebot;
```

## Step 2 (Mac OS only)
#### for mac wiregurard

In case of mac you need wireguard to access the container

`/tmp/jsx wiregurard;`

copy the above wiredgurard command output, the part pertaining the configurations.
Add these configs in the wireguard application then press activate.


### Step 3
Access the docker via the ip that it gives

**note**: For ubuntu users the ip of the container can be retrieved using
`docker inspect 3bot` where 3bot is the default name of the container or the name given
```bash
/tmp/jsx container-shell;
kosmos -p "j.servers.threebot.start(background=True)"
```

### Step 4
To access the content threebot server is providing
#### Mac users

Access in the web browser via the ip that wireguard provided
`WIREGUARD_IP/THREEBOT_PACKAGE_NAME/PACKAGE_NAME`

#### Ubuntu users

Access in web browser via the ip of the docker container

#### to check slides and macros
Check [docs on wikis](https://github.com/threefoldtech/jumpscaleX_threebot/tree/development/ThreeBotPackages/zerobot/webinterface/wiki/wikis)
