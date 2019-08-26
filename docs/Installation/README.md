# JumpscaleX Installation Instructions

## Index

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [After Installation](#after-installation)
- [More Info](#more-info)

### Prerequisites

#### Supported Operating Systems

- Ubuntu 18.04
- macOS 10.7 or newer

#### Required Packages

```bash
# for ubuntu 18.04
apt update -y
apt install -y openssh-server locales curl git rsync unzip lsb python3
```

```bash
# for macOS 10.7 or newer
brew install curl python3 git rsync
```

> To install docker on macOS see this [documentation](https://docs.docker.com/v17.12/docker-for-mac/install/#download-docker-for-mac)

#### Required Python Packages

```bash
pip3 install click
```

#### ssh-agent

ssh-agent loaded with a ssh-key, make sure to add your ssh-key to your github account's authenticated keys

```bash
eval `ssh-agent -s`
ssh-keygen
ssh-add
```

### Installation

#### Download the installer file, change its permission to make it executable

```bash
curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/master/install/jsx.py?$RANDOM > /tmp/jsx;
chmod +x /tmp/jsx;
```

#### To install in container

```bash
/tmp/jsx container-install
```

#### To install in your local system

```bash
/tmp/jsx install
```

> For silent installation: Just add `-s` flag to your install command

## Advanced Installation

it is easy to develop on the installer, will install from existing code on your system

```bash
# create directory, make sure your user has full access to this director (can be a manual step)
mkdir -p /sandbox/code/github/threefoldtech
cd /sandbox/code/github/threefoldtech;
# if you have a permission denied add sudo at the beginning of the command
# then do a sudo chown -R $USER:$USER /sandbox
git clone git@github.com:threefoldtech/jumpscaleX_core.git; cd jumpscaleX_core;
git pull

# link the installer from tmp to the source directory, makes it easy for the rest of this tutorial
rm -f /tmp/jsx.py
rm -f /tmp/InstallTools.py;
ln -s /sandbox/code/github/threefoldtech/jumpscaleX_core/install/jsx.py /tmp/jsx;
ln -s /sandbox/code/github/threefoldtech/jumpscaleX_core/install/InstallTools.py /tmp/InstallTools.py
```

## After Installation

### How to use Jumpscale X

To start JumpcaleX:

#### If you have installed JSX in your system

```bash
source /sandbox/env.sh;
kosmos
```

#### If you have installed JSX in container

The install script has built and started a docker container named `3bot` on your machine.

```bash
# get your kosmos shell (inside your 3bot container)
/tmp/jsx container-kosmos
```

Once kosmos is launched you will see this line:

```bash
JSX>
```

Congrats ! You may now use this jsx shell to manipulate the Jumpscale X library

If jsx is missing from your `/tmp` folder:

```bash
# get the jsx command
curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/master/install/jsx.py?$RANDOM > /tmp/jsx ; \
chmod +x /tmp/jsx;
# get your kosmos shell (inside your 3bot container)
/tmp/jsx container-kosmos
```

## More Info

[more info about the JSX tool](jsx.md)

[init the jumpscale code, can be required after pulling new code](generation.md)
