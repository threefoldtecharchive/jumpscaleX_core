# Install JumpscaleX with Wikis and test macros

## Step 1

### Install jumpscaleX in a container with threebot using the following steps

```bash
curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/master/install/jsx.py > /tmp/jsx;
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
See how to setup a [service account](https://github.com/threefoldtech/jumpscaleX_threebot/blob/master/docs/wikis/tech/service_account.md) and use [gslide macro](https://github.com/threefoldtech/jumpscaleX_threebot/blob/master/docs/wikis/macro/gslide.md).

Then open your browser at `https://your-ip/wiki/testwikis`.
