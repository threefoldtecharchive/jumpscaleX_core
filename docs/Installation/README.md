# Installation Instructions Jumpscale X

## Index
* [I- Installation Prerequisites](#prerequisites)
    - [1- Container](#container-installation)
    - [2- In-System](#insystem-installation)
    - [3- macOS](#macos-installation)
* [II- Container Install](#container-Install)
    - [1- Interactive container](#interactive-container)
    - [2- No Interactive container](#no-interactive-container)
* [III- In-System Install](#insystem-install)
    - [1- Interactive insystem](#interactive-insystem)
    - [2- No Interactive insystem](#no-interactive-insystem)
* [IV- Extra options](#extra-options)
    - [1- reset](#reset)
    - [2- delete](#delete)
    - [3- install with webcomponents](#install-with-webcomponents)
* [V- Advanced Installation](#advanced-installation)
* [VI- After Installation](#after-installation)
* [VII- More Info](#more-info)
## Prerequisites
Before starting the installation make sure to go through the prerequisites. it differs according to your installation type

- ### Container Installation
    This will create a docker-container for you and install jumpscale within it, to install using this method you will need to install
    - os: `Ubuntu 18.04`
    - packages: `curl python3`<br/>
         ```bash
         apt install curl python3
         ```
    - ssh-agent loaded with a ssh-key, make sure to add your ssh-key to your github account's authenticated keys <br/>
        ```bash
        eval `ssh-agent -s`
        ssh-keygen
        ssh-add
        ```
    #### if you are using macOS you will need also to install
    - os: `macOS 10.7 or newer`
    - packages: `docker python3 homebrew git rsync`<br/>
        ```bash
        brew install curl python3 git rsync
        ```
        see: [docker for mac installation](https://docs.docker.com/v17.12/docker-for-mac/install/#download-docker-for-mac)

- ### InSystem Installation
    This will install jumpscale on your local system prefered ubuntu 18:04<br/>
    **Note** This will need more prerequisites 
    - packages: `openssh-server locales curl vim git rsync unzip lsb python3 python3-pip`<br/>
        ```bash
        apt install -y openssh-server locales curl vim git rsync unzip lsb python3 python3-pip
        ```
    - pips: `click`
        ```bash
        pip3 install click
        ```

- ### macOS Installation
    This will install jumpscale on your macOS<br/>
    - os: `macOS 10.7 or newer`
    - packages: `curl python3 git rsync`
        ```bash
        brew install curl python3 git rsync
        ```
        see: [docker for mac installation](https://docs.docker.com/v17.12/docker-for-mac/install/#download-docker-for-mac)
    - pips: `click`
        ```bash
        pip3 install click
        ```

## Container Install
Here we will install jumpscale using container-install option which will create a docker-container for you and install jumpscale within it. we have 2 types of installation as the following<br/>

- #### Interactive Container
    In here you will be asked to provide a secret and to authenticate github cloning in the middle of installation. make sure to add your ssh-key to your github account's authenticated keys
    - #### steps for installation
    - 1- install the prerequisites
    - 2- download the installation file, make it executable, then run it
        ```bash
        # download
        curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX/development_jumpscale/install/jsx.py?$RANDOM > /tmp/jsx;
        # change permission
        chmod +x /tmp/jsx;
        # install
        /tmp/jsx container-install
        ```
- #### No Interactive Container
    This type of installation will install silently and won't ask you about anything

    - 1- install the prerequisites
    - 2- download the installation file, make it executable, configure the installation with your secret, then run it. <br/>
    Note: default sshkey will be the "id_rsa" in `~/.ssh/id_rsa`  so make sure to have one.
        ```bash
        # download
        curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX/development_jumpscale/install/jsx.py?$RANDOM > /tmp/jsx;
        # change permission
        chmod +x /tmp/jsx;
        # configure with your secret - replace mysecret with yours`
        /tmp/jsx configure -s --secret mysecret;
        # install
        /tmp/jsx container-install -s
        ```

## InSystem Install
Here we will install jumpscale using install option which willinstall jumpscale within your local system. we also have 2 types of installation as the following<br/>

- #### Interactive InSystem
    In here you will be asked to provide a secret and to authenticate github cloning in the middle of installation. make sure to add your ssh-key to your github account's authenticated keys

    - 1- install the prerequisites
    - 2- download the installation file, make it executable, then run it
        ```bash
        # download
        curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX/development_jumpscale/install/jsx.py?$RANDOM > /tmp/jsx;
        # change permission
        chmod +x /tmp/jsx; 
        # install
        /tmp/jsx install 
        ```

- #### No Interactive InSystem
    This type of installation won't ask you about anything
    - 1- install the prerequisites
    - 2- download the installation file, make it executable,configure the installation with your secret, then run it <br/>
    Note: default sshkey will be the "id_rsa" in `~/.ssh/id_rsa`  so make sure to have one.
        ```bash
        # download
        curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX/development_jumpscale/install/jsx.py?$RANDOM > /tmp/jsx;
        # change permission
        chmod +x /tmp/jsx; 
        # configure with your secret - replace mysecret with yours`
        /tmp/jsx configure -s --secret mysecret;
        # install
        /tmp/jsx install -s
        ```

## Extra options
also there's some more intersting options to use
- #### reset
    - Will restart the installation
        ```bash
        /tmp/jsx install -r
        ```
- #### delete
    - if you are using a docker this option will delete the existing one
        ```bash
        /tmp/jsx container-install -d
        ```
- #### install with webcomponents
    - installs webcomponents
        ```bash
        /tmp/jsx container-install -w
        ```
- #### jsx command help
    - get more information about other options
        ```bash
        #get more help of jsx command
        /tmp/jsx --help
        ``` 

## Advanced Installation
it is easy to develop on the installer, will install from existing code on your system
```bash
#create directory, make sure your user has full access to this director (can be a manual step)
mkdir -p /sandbox/code/github/threefoldtech
cd /sandbox/code/github/threefoldtech;
#if you have a permission denied add sudo at the beginning of the command
# then do a sudo chown -R $USER:$USER /sandbox
git clone git@github.com:threefoldtech/jumpscaleX.git; cd jumpscaleX;
git checkout master
git pull

#link the installer from tmp to the source directory, makes it easy for the rest of this tutorial
rm -f /tmp/jsx.py
rm -f /tmp/InstallTools.py;
ln -s /sandbox/code/github/threefoldtech/jumpscaleX/install/jsx.py /tmp/jsx;
ln -s /sandbox/code/github/threefoldtech/jumpscaleX/install/InstallTools.py /tmp/InstallTools.py
```

## after-installation
### How to use Jumpscale X

To start JumpcaleX:
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
curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX/development_installer/install/jsx.py?$RANDOM > /tmp/jsx ; \
chmod +x /tmp/jsx; 
# get your kosmos shell (inside your 3bot container)
/tmp/jsx container-kosmos
```

JSX is the main tool for working with a jumpscale deployment

- install
- export/import docker containers
- export BCDB data (coming soon)
- access the kosmos shell in container
- configure your local or container JSX

see [JSX](jsx.md) for more info

## More Info
- [more info about container install](install_docker.md)
- [install in local system (EXPERTS ONLY)](install_insystem.md)
- [more info about the JSX tool](jsx.md)
- [init the jumpscale code, can be required after pulling new code](generation.md)
- [see here OSX requirements specifics](/docs/Installation/install_prerequisites.md#osx)
