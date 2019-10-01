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

copy the above wiredgurard command output, the part pertaining the configurations.
Add these configs in the wireguard application then press activate.



then access the docker via the ip that it gives

`/tmp/jsx container-shell;`
`kosmos -p "j.threebot.package.wikis.start();"`

#### Mac users

check in web browser ip that wireguard give it to you

#### ubuntu users

check in web browser ip of docker container

#### to check slides and macros
How to use gslides: https://github.com/threefoldtech/jumpscaleX_core/blob/d8ab86c405144f7b6811827991f2b97f7a933ccc/docs/tools/wiki/docsites/macros/gslide.md

then via browser: your-ip/wiki/testwikis
