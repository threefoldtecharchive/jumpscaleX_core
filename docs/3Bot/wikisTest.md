# Install JumpscaleX with Wikis and test macros

## Step 1

### Install jumpscaleX in a container with threebot using the following steps

```bash
curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/development/install/jsx.py > /tmp/jsx;
chmod +x /tmp/jsx;
/tmp/jsx container-install -s --threebot;
```

#### for mac wiregurard

In case of mac you need wireguard to access the container

`/tmp/jsx wiregurard;`

then copy wiredgurard that it shows after running the previous command
and add them to wiregurard app's configurations then activate untill
then access the docker via the ip that it gives

`/tmp/jsx container-shell;`
`kosmos -p "j.threebot.package.wikis.start();"`

#### Mac users

check in web browser ip that wireguard give it to you

#### ubuntu users

check in web browser ip of docker container

#### to check slides and macros

your-ip/wiki/testwikis